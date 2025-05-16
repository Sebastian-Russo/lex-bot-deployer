from typing import List, Optional, Dict, Any, Union, TypedDict
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lex as lex
from aws_cdk.aws_lex import CfnBot, CfnBotAlias, CfnBotVersion
from .lex_role import LexRoleProps
from aws_cdk import CfnTag
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import Stack
from constructs import Construct
from .lex_role import LexRole
from .update_neural_engine import UpdateNeuralEngine, UpdateNeuralEngineProps
from .associate_lex_bot import AssociateLexBot
from ..lex_defaults import LexDefaults
from ..utils.hash_code import hash_code
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


class SimpleBot(Construct):
    """
    Defines a simplified interface for creating a lex bot in amazon connect.
    Use this as a pattern or extend/modify/fork this class for more complex cases.
    """

    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 description: Optional[str] = None,
                 locales: List[Dict],
                 role: Optional[iam.IRole] = None,
                 log_group: Optional[logs.LogGroup] = None,
                 audio_bucket: Optional[s3.Bucket] = None,
                 connect_instance_arn: Optional[str] = None,
                 idle_session_ttl_in_seconds: Optional[int] = None,
                 nlu_confidence_threshold: Optional[float] = None,
                 prefix: Optional[str] = None,
                 **kwargs):
        # Only pass scope and id to the Construct base class
        super().__init__(scope, id)

        # Store parameters as instance variables
        self.name = name
        self.description = description
        self.locales = locales
        self.role = role
        self.log_group = log_group
        self.audio_bucket = audio_bucket
        self.connect_instance_arn = connect_instance_arn
        self.region = Stack.of(scope).region
        self.account = Stack.of(scope).account
        self.prefix = prefix  # Store the prefix parameter

        # Ensure we have valid default values
        if idle_session_ttl_in_seconds is None:
            idle_session_ttl_in_seconds = 300  # Default to 5 minutes
        if nlu_confidence_threshold is None:
            nlu_confidence_threshold = 0.75  # Default to 75%

        self.idle_session_ttl_in_seconds = idle_session_ttl_in_seconds
        self.nlu_confidence_threshold = nlu_confidence_threshold

        # Create or use provided role
        self.role = self.role or LexRole(
            self, 'Role',
            props=LexRoleProps(
                lex_log_group_name=self.log_group.log_group_name if self.log_group else None
            )
        )

        # Create bot
        self.bot = CfnBot(
            self, 'Bot',
            name=name[:50],  # Trim to 50 characters
            description=description,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            role_arn=self.role.role_arn,
            data_privacy={"ChildDirected": False},
            bot_locales=self._map_locales(locales, nlu_confidence_threshold),
            auto_build_bot_locales=False,  # Turned off to prevent build issues
            test_bot_alias_settings={
                "botAliasLocaleSettings": self.bot_alias_locales(),
                "conversationLogSettings": self.conversation_log_settings('TestBotAlias')
            },
            # Add the required tag for Connect permissions
            bot_tags=[
                CfnTag(
                    key="AmazonConnectEnabled",
                    value="True"
                )
            ]
        )

        # Create version with hash to ensure updates
        self.version = CfnBotVersion(
            self, f"Version{hash_code({'name': self.name, 'locales': self.locales})}",
            bot_id=self.bot.attr_id,
            bot_version_locale_specification=[{
                "localeId": locale["locale_id"],
                "botVersionLocaleDetails": {
                    "sourceBotVersion": "DRAFT"
                }
            } for locale in self.locales]
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
        for locale in self.locales:
            if locale.get('code_hook') and locale['code_hook'].get('lambda_'):
                locale['code_hook']['lambda_'].add_permission(
                    f"lex-lambda-invoke-{locale['locale_id']}",
                    principal=iam.ServicePrincipal("lexv2.amazonaws.com"),
                    action="lambda:InvokeFunction",
                    source_arn=f"arn:aws:lex:{self.region}:{self.account}:bot/{self.bot.attr_id}/*/*"
                )

        # Associate with connect if provided
        if self.connect_instance_arn:
            # This adds permissions for Connect to invoke Lambda functions
            for locale in self.locales:
                if locale.get('code_hook') and locale['code_hook'].get('lambda_'):
                    locale['code_hook']['lambda_'].add_permission(
                        f"connect-lambda-invoke-{locale['locale_id']}",
                        principal=iam.ServicePrincipal("connect.amazonaws.com"),
                        action="lambda:InvokeFunction",
                        source_arn=f"arn:aws:connect:{self.region}:{self.account}:instance/*"
                    )

            AssociateLexBot(
                self, 'Association',
                connect_instance_arn=self.connect_instance_arn,
                alias=self.alias
            )

        # Update neural engine for locales that need it
        neural_locales = [l for l in self.locales if (l.get('engine') or LexDefaults.engine) == 'neural']
        for l in neural_locales:
            id = f"{l['locale_id']}Neural"
            # Create UpdateNeuralEngineProps instance
            props = UpdateNeuralEngineProps(
                bot_id=self.bot.attr_id,
                description=l.get('description'),
                locale_id=l['locale_id'],
                nlu_intent_confidence_threshold=self.nlu_confidence_threshold,
                voice_id=l['voice_id']
            )

            # Pass the props object
            engine_update = UpdateNeuralEngine(
                self, id, props=props
            )
            self.version.node.add_dependency(engine_update)
            self.alias.node.add_dependency(engine_update)

    def _map_locales(self, locales, nlu_confidence_threshold: float):
        """Map SimpleLocale objects to the format expected by CfnBot"""
        return [self._format_locale(l, nlu_confidence_threshold) for l in locales]

    def _format_locale(self, locale: SimpleLocale, nlu_confidence_threshold: float):
        """Format a single locale for CfnBot"""
        # Get code hooks from locale using safe access
        code_hook = locale.get('code_hook', {})
        dialog_code_hook = code_hook.get('dialog', False)
        fulfillment_code_hook = code_hook.get('fulfillment', False)

        return {
            "localeId": locale['locale_id'],
            "description": locale.get('description'),
            "nluConfidenceThreshold": nlu_confidence_threshold,
            "voiceSettings": {
                "voiceId": locale['voice_id']
            },
            "intents": self._format_intents(locale['intents']),
            "botLocaleSetting": {
                "enabled": True,
                "codeHookSpecification": {
                    "lambdaCodeHook": {
                        "codeHookInterfaceVersion": "1.0",
                        "lambdaArn": locale['code_hook']['lambda_'].function_arn
                    }
                } if code_hook.get('lambda_') else None
            }
        }

    def _format_intents(self, intents: List[SimpleIntent]):
        """
        Format a list of SimpleIntent objects into the structure expected by Lex CfnBot.
        This matches the logic of the provided TypeScript reference.
        """
        formatted_intents = []

        # Try to get code hook settings from self.locales if possible
        # (Assume the current locale is being processed and code_hook is available as self.code_hook or similar)
        # If not, default to False
        dialog_code_hook = False
        fulfillment_code_hook = False
        code_hook = getattr(self, 'code_hook', None)
        if code_hook:
            dialog_code_hook = getattr(code_hook, 'dialog', False)
            fulfillment_code_hook = getattr(code_hook, 'fulfillment', False)

        for intent in intents:
            # Prepare slot priorities if slots exist
            slot_priorities = None
            slots = intent.get("slots")
            if slots:
                slot_priorities = [
                    {"slotName": slot.get("name"), "priority": idx + 1}
                    for idx, slot in enumerate(slots)
                ]

            formatted = {
                "name": intent.get("name"),
                "dialogCodeHook": {"enabled": dialog_code_hook},
                "fulfillmentCodeHook": {
                    "enabled": fulfillment_code_hook,
                    "postFulfillmentStatusSpecification": self._post_fulfillment_prompt(
                        {"value": intent.get("fulfillment_prompt")} if intent.get("fulfillment_prompt") else None
                    ),
                },
                "sampleUtterances": [{"utterance": u} for u in intent.get("utterances", [])],
                "slotPriorities": slot_priorities,
                "slots": self._transform_slots({"slots": slots}) if slots else [],
                "intentConfirmationSetting": self._transform_intent_confirmation(
                    {"message_groups": [{"message": intent.get("confirmation_prompt")}]} if intent.get("confirmation_prompt") else {}
                ) if intent.get("confirmation_prompt") else None,
            }
            formatted_intents.append(formatted)

        # Add fallback intent
        fallback_intent = {
            "name": "FallbackIntent",
            "dialogCodeHook": {"enabled": dialog_code_hook},
            "fulfillmentCodeHook": {"enabled": fulfillment_code_hook},
            "parentIntentSignature": "AMAZON.FallbackIntent",
        }
        formatted_intents.append(fallback_intent)

        return formatted_intents


    def _transform_slot_type(self, slot_type: dict) -> dict:
        """Transform slot type dictionary to Lex format"""
        return {
            "name": slot_type.get("name"),
            "description": slot_type.get("description"),
            "slot_type_name": slot_type.get("name"),
            "external_source_setting": {
                "grammar_slot_type_setting": {
                    "source": slot_type.get("grammar_source")
                }
            } if slot_type.get("grammar_source") else None,
            "slot_type_values": [{"sample_value": {"value": v}} for v in slot_type.get("values", [])],
            "value_selection_setting": {
                "resolution_strategy": slot_type.get("resolution_strategy", "OriginalValue")
            }
        }

    def _transform_slots(self, intent: dict) -> List[dict]:
        """Transform intent slots to Lex format"""
        return [{
            "name": slot.get("name"),
            "description": slot.get("description"),
            "slotTypeName": slot.get("slot_type_name"),  # Match TypeScript input format
            "valueElicitationSetting": {
                "slotConstraint": "Required" if slot.get("required") else "Optional",
                "promptSpecification": {
                    "allowInterrupt": slot.get("allow_interrupt", True),
                    "maxRetries": slot.get("max_retries", 2),
                    "messageGroupsList": [
                        {
                            "message": {
                                "plainTextMessage": {
                                    "value": message
                                }
                            }
                        } for message in slot.get("elicitation_messages", [])
                    ]
                },
                "sampleUtterances": [{"utterance": u} for u in slot.get("sample_utterances", [])]
            },
            "obfuscationSetting": {
                "obfuscationSettingType": "None"
            }
        } for slot in intent.get("slots", [])]

    def _transform_intent_confirmation(self, prompt) -> Optional[dict]:
        """Transform a confirmation prompt to the full AWS structure"""
        if not prompt:
            return None

        # If prompt is already a dictionary, extract the message
        if isinstance(prompt, dict) and 'message_groups' in prompt:
            message_groups = prompt.get('message_groups', [])
            if message_groups and isinstance(message_groups[0], dict):
                prompt = message_groups[0].get('message', '')
        # If prompt is a dictionary-like string, extract the message
        elif isinstance(prompt, str) and prompt.startswith('{') and 'message' in prompt:
            try:
                # Try to extract message from a dictionary-like string
                import ast
                prompt_dict = ast.literal_eval(prompt)
                if isinstance(prompt_dict, dict) and 'message_groups' in prompt_dict:
                    message_groups = prompt_dict.get('message_groups', [])
                    if message_groups and isinstance(message_groups[0], dict):
                        prompt = message_groups[0].get('message', prompt)
            except:
                # If parsing fails, use the original prompt
                pass

        return {
            "promptSpecification": {
                "maxRetries": 3,
                "messageGroupsList": [
                    {
                        "message": {
                            "plainTextMessage": {
                                "value": str(prompt)  # Just the plain message
                            }
                        }
                    }
                ],
                # "allowInterrupt": True
            }
        }

    # TODO: messageGroupsList OR message_groups_list ?
    def _post_fulfillment_prompt(self, prompt: dict) -> dict:
        """Transform prompt dictionary to Lex format"""
        if not prompt:
            return None

        return {
            "success_response": {
                "message_groups_list": [{
                    "message": {
                        "plain_text_message": {
                            "value": prompt.get("value")
                        }
                    }
                }]
            }
        }

    def bot_alias_locales(self):
        """Return bot alias locale settings"""
        return [{
            "localeId": locale["locale_id"],  # camelCase output for AWS
            "botAliasLocaleSetting": {  # camelCase output for AWS
                "enabled": True,
            # Add code hook if lambda is provided - matches TypeScript logic
            "codeHookSpecification": {
                "lambdaCodeHook": {
                    "codeHookInterfaceVersion": "1.0",
                    "lambdaArn": locale["code_hook"]["lambda_"].function_arn
                }
            } if locale.get("code_hook") and locale["code_hook"].get("lambda_") else None
        }
    } for locale in self.locales]

    def conversation_log_settings(self, alias_name: str):
        """Return conversation log settings"""
        # Return None if neither log group nor audio bucket exists
        if not self.log_group and not self.audio_bucket:
            return None

        settings = {}

        # Add audio log settings if audio bucket exists
        if self.audio_bucket:
            settings["audioLogSettings"] = [
                {
                    "enabled": True,
                    "destination": {
                        "s3Bucket": {
                            "s3BucketArn": self.audio_bucket.bucket_arn,
                            "logPrefix": f"{self.name}/{alias_name}"
                            # "kmsKeyArn": "todo"  # Commented out like in TS version
                        }
                    }
                }
            ]

        # Add text log settings if log group exists
        if self.log_group:
            settings["textLogSettings"] = [
                {
                    "enabled": True,
                    "destination": {
                        "cloudWatch": {
                            "cloudWatchLogGroupArn": self.log_group.log_group_arn,
                            "logPrefix": f"{self.name}/{alias_name}"
                        }
                    }
                }
            ]

        return settings
