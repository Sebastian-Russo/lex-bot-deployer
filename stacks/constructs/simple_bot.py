from threading import local
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
from typing import List, Optional

@dataclass
class CodeHook:
    lambda_: lambda_.IFunction
    dialog: bool = False
    fulfillment: bool = False

@dataclass
class SimpleSlot:
    name: str
    slot_type_name: str
    elicitation_messages: List[str]
    description: Optional[str]
    allow_interrupt: bool = False
    max_retries: int = 3
    required: bool = False

    def to_cdk_slot(self) -> CfnBot.SlotProperty:
        return CfnBot.SlotProperty(
            name=self.name,
            description=self.description,
            slot_type_name=self.slot_type_name,  # Match TypeScript input format
            value_elicitation_setting=CfnBot.SlotValueElicitationSettingProperty(
                slot_constraint="Required" if self.required else "Optional",
                prompt_specification=CfnBot.PromptSpecificationProperty(
                    allow_interrupt=self.allow_interrupt,
                    max_retries=self.max_retries,
                    message_groups_list=[
                        {
                            "message": {
                                "plain_text_message": {
                                    "value": message
                                }
                            }
                        } for message in self.elicitation_messages
                    ]
                )
            )
        )
    
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

    def to_cdk_intent(self, dialog_code_hook: bool, fulfillment_code_hook: bool) -> CfnBot.IntentProperty:
        # Prepare slot priorities if slots exist
        slot_priorities: List[CfnBot.SlotPriorityProperty] = None
        if self.slots:
            slot_priorities = [
                {
                    "slot_name": slot.name,
                    "priority": idx + 1
                }
                for idx, slot in enumerate(self.slots)
            ]

        slots: List[CfnBot.SlotProperty] = []
        if self.slots:
            slots = [slot.to_cdk_slot() for slot in self.slots]

        return CfnBot.IntentProperty(
            name=self.name,
            dialog_code_hook={
                "enabled": dialog_code_hook,
            },
            fulfillment_code_hook= {
                "enabled": fulfillment_code_hook,
                "fulfillment_updates_specification": self._post_fulfillment_prompt(self.fulfillment_prompt),
            },
            sample_utterances= [{"utterance": u} for u in self.utterances],
            slot_priorities= slot_priorities,
            slots = slots,
            intent_confirmation_setting= self._transform_intent_confirmation(self.confirmation_prompt),
        )

    def _transform_intent_confirmation(self, prompt: str) -> Optional[CfnBot.IntentConfirmationSettingProperty]:
        if not prompt:
            return None

        return CfnBot.IntentConfirmationSettingProperty(
            prompt_specification=CfnBot.PromptSpecificationProperty(
                max_retries=3,
                message_groups_list=[
                    CfnBot.MessageGroupProperty({
                        "message": {
                            "plain_text_message": {
                                "value": prompt
                            }
                        }
                    })
                ]
            )
        )    

    def _post_fulfillment_prompt(self, prompt: str) -> Optional[CfnBot.PostFulfillmentStatusSpecificationProperty]:
        if not prompt:
            return None

        return CfnBot.PostFulfillmentStatusSpecificationProperty(
            success_response=CfnBot.PostFulfillmentStatusSpecificationProperty.SuccessResponseProperty(
                message_groups_list=[{
                    "message": {
                        "plain_text_message": {
                            "value": prompt
                        }
                    }
                }]  
            )
        )

@dataclass
class SimpleLocale:
    locale_id: str
    voice_id: str
    intents: List[SimpleIntent]
    description: Optional[str] = None
    engine: Optional[str] = None
    slot_types: Optional[List[SimpleSlotType]] = None
    code_hook: Optional[CodeHook] = None

    def to_cdk_locale(self, nlu_confidence_threshold: float) -> CfnBot.BotLocaleProperty:
        dialog_code_hook = False
        fulfillment_code_hook = False
        if self.code_hook:
            dialog_code_hook = self.code_hook.dialog
            fulfillment_code_hook = self.code_hook.fulfillment

        intents = [intent.to_cdk_intent(dialog_code_hook, fulfillment_code_hook) for intent in self.intents]
        intents.append(CfnBot.IntentProperty(
            name='FallbackIntent',
            dialog_code_hook={ "enabled": dialog_code_hook },
            fulfillment_code_hook={ "enabled": fulfillment_code_hook },
            parent_intent_signature= 'AMAZON.FallbackIntent',
        ))

        return CfnBot.BotLocaleProperty(
            locale_id=self.locale_id,
            nlu_confidence_threshold=nlu_confidence_threshold,
            voice_settings={
                "voiceId": self.voice_id
            },
            # TODO: Implement Slot Types
            intents=intents,
        )

    def to_cdk_bot_alias_locale_setting(self) -> CfnBotAlias.BotAliasLocaleSettingsItemProperty:
        code_hook_specification = None
        if(self.code_hook is not None):
            code_hook_specification = CfnBotAlias.CodeHookSpecificationProperty(
                lambda_code_hook={
                    'code_hook_interface_version': '1.0',
                    'lambda_arn': self.code_hook.lambda_.function_arn
                }
            )

        return CfnBotAlias.BotAliasLocaleSettingsItemProperty(
            bot_alias_locale_setting=CfnBotAlias.BotAliasLocaleSettingsProperty(
                enabled=True,
                code_hook_specification=code_hook_specification
            ),
            locale_id=self.locale_id
        )



class SimpleBot(Construct):
    """
    Defines a simplified interface for creating a lex bot in amazon connect.
    Use this as a pattern or extend/modify/fork this class for more complex cases.
    """

    def __init__(self, scope: Construct, id: str, *,
                 name: str,
                 description: Optional[str] = None,
                 locales: List[SimpleLocale],
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

        version_id = f'Version{hash_code(self)}'

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
            name=self.name[:50],  # Trim to 50 characters
            description=self.description,
            idle_session_ttl_in_seconds=self.idle_session_ttl_in_seconds,
            role_arn=self.role.role_arn,
            data_privacy={"ChildDirected": False},
            bot_locales=[l.to_cdk_locale(self.nlu_confidence_threshold) for l in self.locales],
            auto_build_bot_locales=False,  # Turned off to prevent build issues
            test_bot_alias_settings={
                "bot_alias_locale_settings": self.to_bot_alias_locale_settings(),
                "conversation_log_settings": self.conversation_log_settings('TestBotAlias')
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
            self, version_id,
            bot_id=self.bot.attr_id,
            bot_version_locale_specification=[CfnBotVersion.BotVersionLocaleSpecificationProperty(
                locale_id=locale.locale_id,
                bot_version_locale_details=CfnBotVersion.BotVersionLocaleDetailsProperty(
                    source_bot_version="DRAFT"
                )
            ) for locale in self.locales]
        )

        # Create alias
        self.alias = CfnBotAlias(
            self, 'Alias',
            bot_alias_name='live',
            bot_id=self.bot.attr_id,
            bot_alias_locale_settings=self.to_bot_alias_locale_settings(),
            bot_version=self.version.attr_bot_version,
            conversation_log_settings=self.conversation_log_settings('live')
        )

        # Add permissions for lambdas
        for locale in self.locales:
            if locale.code_hook and locale.code_hook.lambda_:
                locale.code_hook.lambda_.add_permission(
                    f"lex-lambda-invoke-{locale.locale_id}",
                    principal=iam.ServicePrincipal("lexv2.amazonaws.com"),
                    action="lambda:InvokeFunction",
                    source_arn=f"arn:aws:lex:{self.region}:{self.account}:bot/{self.bot.attr_id}/*/*"
                )

        # Associate with connect if provided
        if self.connect_instance_arn:
            # This adds permissions for Connect to invoke Lambda functions
            for locale in self.locales:
                if locale.code_hook and locale.code_hook.lambda_:
                    locale.code_hook.lambda_.add_permission(
                        f"connect-lambda-invoke-{locale.locale_id}",
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
        neural_locales = [l for l in self.locales if (l.engine or LexDefaults.engine) == 'neural']
        for l in neural_locales:
            id = f"{l.locale_id}Neural"
            # Create UpdateNeuralEngineProps instance
            props = UpdateNeuralEngineProps(
                bot_id=self.bot.attr_id,
                description=l.description,
                locale_id=l.locale_id,
                nlu_intent_confidence_threshold=self.nlu_confidence_threshold,
                voice_id=l.voice_id
            )

            # Pass the props object
            engine_update = UpdateNeuralEngine(
                self, id, props=props
            )
            self.version.node.add_dependency(engine_update)
            self.alias.node.add_dependency(engine_update)

    def to_bot_alias_locale_settings(self) -> List[CfnBotAlias.BotAliasLocaleSettingsItemProperty]:
        return [locale.to_cdk_bot_alias_locale_setting() for locale in self.locales]

    # Rest of the class remains unchanged
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

    def conversation_log_settings(self, alias_name: str) -> Optional[CfnBotAlias.ConversationLogSettingsProperty]:
        """Return conversation log settings"""
        # Return None if neither log group nor audio bucket exists
        if not self.log_group and not self.audio_bucket:
            return None

        audio_setting: CfnBotAlias.AudioLogSettingProperty = None
        log_settings: CfnBotAlias.TextLogSettingProperty = None

        # Add audio log settings if audio bucket exists
        if self.audio_bucket:
            audio_setting = [
                CfnBotAlias.AudioLogSettingProperty(
                    enabled=True,
                    destination=CfnBotAlias.AudioLogDestinationProperty(
                        s3_bucket=CfnBotAlias.S3BucketLogDestinationProperty(
                            s3_bucket_arn=self.audio_bucket.bucket_arn,
                            log_prefix=f"{self.name}/{alias_name}",
                            # "kmsKeyArn": "todo"
                        )
                    )
                )
            ]

        # Add text log settings if log group exists
        if self.log_group:
            log_settings = [
                CfnBotAlias.TextLogSettingProperty(
                    enabled=True,
                    destination=CfnBotAlias.TextLogDestinationProperty(
                        cloud_watch=CfnBotAlias.CloudWatchLogGroupLogDestinationProperty(
                            cloud_watch_log_group_arn=self.log_group.log_group_arn,
                            log_prefix=f"{self.name}/{alias_name}"
                        )
                    )
                )
            ]

        return CfnBotAlias.ConversationLogSettingsProperty(
            audio_log_settings=audio_setting,
            text_log_settings=log_settings,
        )