from typing import List, Optional, Dict, Any, Union
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lex as lex
from aws_cdk.aws_lex import CfnBot, CfnBotAlias, CfnBotVersion
from constructs import Construct
from .lex_role import LexRole
from .update_neural_engine import UpdateNeuralEngine
from .associate_lex_bot import AssociateLexBot
from lex_defaults import LexDefaults
from dataclasses import dataclass
from typing import TypedDict, List, Optional


@dataclass
class SimpleSlot:
    name: str
    slot_type_name: str
    description: Optional[str] = None
    elicitation_messages: List[str] = None
    allow_interrupt: Optional[bool] = None
    max_retries: Optional[int] = None
    required: Optional[bool] = None


@dataclass
class SimpleSlotTypeValue:
    sample_value: str
    synonyms: Optional[List[str]] = None


@dataclass
class SimpleSlotType:
    name: str
    values: List[SimpleSlotTypeValue]
    description: Optional[str] = None
    resolution_strategy: Optional[str] = None


@dataclass
class SimpleIntent:
    name: str
    utterances: List[str]
    slots: Optional[List[SimpleSlot]] = None
    confirmation_prompt: Optional[str] = None
    fulfillment_prompt: Optional[str] = None


@dataclass
class CodeHook:
    lambda_: lambda_.IFunction
    dialog: bool = False
    fulfillment: bool = False


@dataclass
class SimpleLocale:
    locale_id: str
    voice_id: str
    intents: List[SimpleIntent]
    description: Optional[str] = None
    engine: Optional[str] = None
    slot_types: Optional[List[SimpleSlotType]] = None
    code_hook: Optional[CodeHook] = None


class SimpleBotProps:
    def __init__(
        self,
        name: str,
        locales: List[SimpleLocale],
        connect_instance_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
    ):
        self.name = name
        self.description = description
        self.locales = locales
        self.role = role
        self.idle_session_ttl_in_seconds = idle_session_ttl_in_seconds
        self.nlu_confidence_threshold = nlu_confidence_threshold
        self.connect_instance_arn = connect_instance_arn
        self.log_group = log_group
        self.audio_bucket = audio_bucket


class SimpleBot(Construct):
    """
    Defines a simplified interface for creating a lex bot in amazon connect.
    Use this as a pattern or extend/modify/fork this class for more complex cases.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        props: SimpleBotProps
    ):
        super().__init__(scope, id)
        self.props = props

        name = props.name
        description = props.description
        locales = props.locales
        idle_session_ttl_in_seconds = props.idle_session_ttl_in_seconds or LexDefaults.idle_session_ttl_in_seconds
        nlu_confidence_threshold = props.nlu_confidence_threshold or LexDefaults.nlu_confidence_threshold
        log_group = props.log_group
        connect_instance_arn = props.connect_instance_arn

        # Create or use provided role
        self.role = props.role or LexRole(
            self, 'Role',
            lex_log_group_name=log_group.log_group_name if log_group else None
        )

        # Create bot
        self.bot = CfnBot(
            self, 'Bot',
            name=name[:50],  # Trim to 50 characters
            description=description,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            role_arn=self.role.role_arn,
            data_privacy={"child_directed": False},
            bot_locales=self._map_locales(locales, nlu_confidence_threshold),
            auto_build_bot_locales=False,  # Turned off to prevent build issues
            test_bot_alias_settings={
                "bot_alias_locale_settings": self.bot_alias_locales(),
                "conversation_log_settings": self.conversation_log_settings('TestBotAlias')
            }
        )

        # Create version with hash to ensure updates
        self.version = CfnBotVersion(
            self, f"Version{hash_code(self.props)}",
            bot_id=self.bot.attr_id,
            bot_version_locale_specification=[{
                "locale_id": l.locale_id,
                "bot_version_locale_details": {
                    "source_bot_version": "DRAFT"
                }
            } for l in locales]
        )

        # Create alias
        self.alias = CfnBotAlias(
            self, 'Alias',
            bot_alias_name='live',
            bot_id=self.bot.attr_id,
            bot_alias_locale_settings=self.bot_alias_locales(),
            bot_version=self.version.attr_bot_version,
            conversation_log_settings=self.conversation_log_settings('live')
        )

        # Add permissions for lambdas
        for l in props.locales:
            if l.code_hook and l.code_hook.lambda_:
                l.code_hook.lambda_.add_permission(
                    f"lex-lambda-invoke-{l.locale_id}",
                    principal=iam.ServicePrincipal('lexv2.amazonaws.com'),
                    action='lambda:InvokeFunction',
                    source_arn=self.alias.attr_arn
                )

        # Update neural engine for locales that need it
        neural_locales = [l for l in props.locales if (l.engine or LexDefaults.engine) == 'neural']
        for l in neural_locales:
            id = f"{l.locale_id}Neural"
            engine_update = UpdateNeuralEngine(
                self, id,
                bot_id=self.bot.attr_id,
                description=l.description,
                locale_id=l.locale_id,
                nlu_intent_confidence_threshold=nlu_confidence_threshold,
                voice_id=l.voice_id
            )
            self.version.node.add_dependency(engine_update)
            self.alias.node.add_dependency(engine_update)

        # Associate bot with Connect instance
        AssociateLexBot(
            self, 'Association',
            connect_instance_arn=connect_instance_arn,
            alias=self.alias
        )

    def _map_locales(self, locales, nlu_confidence_threshold):
        """Map SimpleLocale objects to the format expected by CfnBot"""
        return [self._format_locale(l, nlu_confidence_threshold) for l in locales]

    def _format_locale(self, locale, nlu_confidence_threshold):
        """Format a single locale for CfnBot"""
        dialog_code_hook = locale.code_hook.dialog if locale.code_hook else False
        fulfillment_code_hook = locale.code_hook.fulfillment if locale.code_hook else False

        return {
            "locale_id": locale.locale_id,
            "nlu_confidence_threshold": nlu_confidence_threshold,
            "voice_settings": {
                "voice_id": locale.voice_id
            },
            "slot_types": [self._transform_slot_type(s) for s in (locale.slot_types or [])],
            "intents": [
                *[{
                    "name": intent.name,
                    "dialog_code_hook": {"enabled": dialog_code_hook},
                    "fulfillment_code_hook": {
                        "enabled": fulfillment_code_hook,
                        "post_fulfillment_status_specification": self._post_fulfillment_prompt(intent.fulfillment_prompt)
                    },
                    "sample_utterances": [{"utterance": u} for u in intent.utterances],
                    "slot_priorities": [{"slot_name": slot.name, "priority": i + 1}
                                       for i, slot in enumerate(intent.slots or [])],
                    "slots": self._transform_slots(intent),
                    "intent_confirmation_setting": self._transform_intent_confirmation(intent.confirmation_prompt)
                } for intent in locale.intents],
                {
                    "name": "FallbackIntent",
                    "dialog_code_hook": {"enabled": dialog_code_hook},
                    "fulfillment_code_hook": {"enabled": fulfillment_code_hook},
                    "parent_intent_signature": "AMAZON.FallbackIntent"
                }
            ]
        }

    def _transform_slot_type(self, slot_type: SimpleSlotType) -> dict:
        """Transform a SimpleSlotType to CfnBot.SlotTypeProperty"""
        return {
            "name": slot_type.name,
            "slot_type_values": [{
                "sample_value": {"value": v.sample_value},
                "synonyms": [{"value": s} for s in (v.synonyms or [])]
            } for v in slot_type.values],
            "value_selection_setting": {
                "resolution_strategy": slot_type.resolution_strategy or "ORIGINAL_VALUE"
            },
            "description": slot_type.description or ""
        }

    def _transform_slots(self, intent: SimpleIntent) -> List[dict]:
        """Transform SimpleSlot list to CfnBot.SlotProperty list"""
        if not intent.slots:
            return []

        return [{
            "name": slot.name,
            "slot_type_name": slot.slot_type_name,
            "description": slot.description,
            "value_elicitation_setting": {
                "slot_constraint": "Required" if slot.required else "Optional",
                "prompt_specification": {
                    "allow_interrupt": slot.allow_interrupt if slot.allow_interrupt is not None else LexDefaults.slot_allow_interrupt,
                    "max_retries": slot.max_retries if slot.max_retries is not None else LexDefaults.slot_retries,
                    "message_groups_list": [{
                        "message": {
                            "plain_text_message": {
                                "value": message
                            }
                        }
                    } for message in slot.elicitation_messages]
                }
            }
        } for slot in intent.slots]

    def _transform_intent_confirmation(self, prompt: Optional[str]) -> Optional[dict]:
        """Transform confirmation prompt to IntentConfirmationSettingProperty"""
        if not prompt:
            return None

        return {
            "prompt_specification": {
                "max_retries": 3,
                "message_groups_list": [{
                    "message": {
                        "plain_text_message": {
                            "value": prompt
                        }
                    }
                }]
            }
        }

    def _post_fulfillment_prompt(self, prompt: Optional[str]) -> Optional[dict]:
        """Transform fulfillment prompt to PostFulfillmentStatusSpecificationProperty"""
        if not prompt:
            return None

        return {
            "success_response": {
                "message_groups_list": [{
                    "message": {
                        "plain_text_message": {
                            "value": prompt
                        }
                    }
                }]
            }
        }

    def bot_alias_locales(self) -> List[dict]:
        """Generate BotAliasLocaleSettingsItemProperty list"""
        return [{
            "bot_alias_locale_setting": {
                "enabled": True,
                "code_hook_specification": {
                    "lambda_code_hook": {
                        "code_hook_interface_version": "1.0",
                        "lambda_arn": l.code_hook.lambda_.function_arn
                    }
                } if l.code_hook and l.code_hook.lambda_ else None
            },
            "locale_id": l.locale_id
        } for l in self.props.locales]

    def conversation_log_settings(self, alias_name: str) -> Optional[dict]:
        """Generate ConversationLogSettingsProperty"""
        log_group = self.props.log_group
        audio_bucket = self.props.audio_bucket
        name = self.props.name

        if not log_group and not audio_bucket:
            return None

        settings = {}

        if log_group:
            settings["text_log_settings"] = [{
                "enabled": True,
                "destination": {
                    "cloud_watch": {
                        "cloud_watch_log_group_arn": log_group.log_group_arn,
                        "log_prefix": f"{name}/{alias_name}"
                    }
                }
            }]

        if audio_bucket:
            settings["audio_log_settings"] = [{
                "enabled": True,
                "destination": {
                    "s3_bucket": {
                        "s3_bucket_arn": audio_bucket.bucket_arn,
                        "log_prefix": f"{name}/{alias_name}"
                    }
                }
            }]

        return settings