from dataclasses import dataclass
from typing import List, Optional

from aws_cdk import CfnTag, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_lex import CfnBot, CfnBotAlias, CfnBotVersion
from constructs import Construct

from ..utils.hash_code import hash_code
from .associate_lex_bot import AssociateLexBot
from .lex_role import LexRole, LexRoleProps


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
    description: str = ''
    allow_interrupt: bool = False
    max_retries: int = 3
    required: bool = False

    def to_cdk_slot(self) -> CfnBot.SlotProperty:
        return CfnBot.SlotProperty(
            name=self.name,
            description=self.description,
            slot_type_name=self.slot_type_name,  # Match TypeScript input format
            value_elicitation_setting=CfnBot.SlotValueElicitationSettingProperty(
                slot_constraint='Required' if self.required else 'Optional',
                prompt_specification=CfnBot.PromptSpecificationProperty(
                    allow_interrupt=self.allow_interrupt,
                    max_retries=self.max_retries,
                    message_groups_list=[
                        CfnBot.MessageGroupProperty(
                            message=CfnBot.MessageProperty(
                                plain_text_message=CfnBot.PlainTextMessageProperty(
                                    value=message
                                )
                            )
                        )
                        for message in self.elicitation_messages
                    ],
                ),
            ),
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

    def to_cdk_intent(
        self, dialog_code_hook: bool, fulfillment_code_hook: bool
    ) -> CfnBot.IntentProperty:
        # Prepare slot priorities if slots exist
        slot_priorities: List[CfnBot.SlotPriorityProperty] = None
        if self.slots:
            slot_priorities = [
                {'slotName': slot.name, 'priority': idx + 1}
                for idx, slot in enumerate(self.slots)
            ]

        slots: List[CfnBot.SlotProperty] = []
        if self.slots:
            slots = [slot.to_cdk_slot() for slot in self.slots]

        return CfnBot.IntentProperty(
            name=self.name,
            dialog_code_hook={
                'enabled': dialog_code_hook,
            },
            fulfillment_code_hook={
                'enabled': fulfillment_code_hook,
                'fulfillment_updates_specification': self._post_fulfillment_prompt(
                    self.fulfillment_prompt
                ),
            },
            sample_utterances=[{'utterance': u} for u in self.utterances],
            slot_priorities=slot_priorities,
            slots=slots,
            intent_confirmation_setting=self._transform_intent_confirmation(
                self.confirmation_prompt
            ),
        )

    def _transform_intent_confirmation(
        self, prompt: str
    ) -> Optional[CfnBot.IntentConfirmationSettingProperty]:
        if not prompt:
            return None

        return CfnBot.IntentConfirmationSettingProperty(
            prompt_specification=CfnBot.PromptSpecificationProperty(
                max_retries=3,
                message_groups_list=[
                    CfnBot.MessageGroupProperty(
                        message=CfnBot.MessageProperty(
                            plain_text_message=CfnBot.PlainTextMessageProperty(
                                value=prompt
                            )
                        )
                    )
                ],
            )
        )

    def _post_fulfillment_prompt(
        self, prompt: str
    ) -> Optional[CfnBot.PostFulfillmentStatusSpecificationProperty]:
        if not prompt:
            return None

        return CfnBot.PostFulfillmentStatusSpecificationProperty(
            success_response=CfnBot.ResponseSpecificationProperty(
                message_groups_list=[
                    CfnBot.MessageGroupProperty(
                        message=CfnBot.MessageProperty(
                            plain_text_message=CfnBot.PlainTextMessageProperty(
                                value=prompt
                            )
                        )
                    )
                ]
            )
        )


@dataclass
class SimpleLocale:
    locale_id: str
    voice_id: str
    intents: List[SimpleIntent]
    description: Optional[str] = None
    engine: Optional[str] = 'neural'
    slot_types: Optional[List[SimpleSlotType]] = None
    code_hook: Optional[CodeHook] = None

    def to_cdk_locale(
        self, nlu_confidence_threshold: float
    ) -> CfnBot.BotLocaleProperty:
        dialog_code_hook = False
        fulfillment_code_hook = False
        if self.code_hook:
            dialog_code_hook = self.code_hook.dialog
            fulfillment_code_hook = self.code_hook.fulfillment

        intents = [
            intent.to_cdk_intent(dialog_code_hook, fulfillment_code_hook)
            for intent in self.intents
        ]
        intents.append(
            CfnBot.IntentProperty(
                name='FallbackIntent',
                dialog_code_hook={'enabled': dialog_code_hook},
                fulfillment_code_hook={'enabled': fulfillment_code_hook},
                parent_intent_signature='AMAZON.FallbackIntent',
            )
        )

        return CfnBot.BotLocaleProperty(
            locale_id=self.locale_id,
            nlu_confidence_threshold=nlu_confidence_threshold,
            voice_settings={'voiceId': self.voice_id, 'engine': self.engine},
            # TODO: Implement Slot Types
            intents=intents,
        )

    def to_cdk_bot_locale_setting(self) -> CfnBot.BotAliasLocaleSettingsItemProperty:
        code_hook_specification = None
        if self.code_hook is not None:
            code_hook_specification = CfnBot.CodeHookSpecificationProperty(
                lambda_code_hook={
                    'codeHookInterfaceVersion': '1.0',
                    'lambdaArn': self.code_hook.lambda_.function_arn,
                }
            )

        return CfnBot.BotAliasLocaleSettingsItemProperty(
            bot_alias_locale_setting=CfnBot.BotAliasLocaleSettingsProperty(
                enabled=True, code_hook_specification=code_hook_specification
            ),
            locale_id=self.locale_id,
        )

    def to_cdk_bot_alias_locale_setting(
        self,
    ) -> CfnBotAlias.BotAliasLocaleSettingsItemProperty:
        code_hook_specification = None
        if self.code_hook is not None:
            code_hook_specification = CfnBotAlias.CodeHookSpecificationProperty(
                lambda_code_hook={
                    'codeHookInterfaceVersion': '1.0',
                    'lambdaArn': self.code_hook.lambda_.function_arn,
                }
            )

        return CfnBotAlias.BotAliasLocaleSettingsItemProperty(
            bot_alias_locale_setting=CfnBotAlias.BotAliasLocaleSettingsProperty(
                enabled=True, code_hook_specification=code_hook_specification
            ),
            locale_id=self.locale_id,
        )


@dataclass
class SimpleBotProps:
    name: str
    locales: List[SimpleLocale]
    description: Optional[str] = None
    role: Optional[iam.IRole] = None
    log_group: Optional[logs.LogGroup] = None
    audio_bucket: Optional[s3.Bucket] = None
    connect_instance_arn: Optional[str] = None
    idle_session_ttl_in_seconds: int = 300
    nlu_confidence_threshold: float = 0.75
    prefix: Optional[str] = None


class SimpleBot(Construct):
    """
    Defines a simplified interface for creating a lex bot in amazon connect.
    Use this as a pattern or extend/modify/fork this class for more complex cases.
    """

    def __init__(self, scope: Construct, id: str, *, props: SimpleBotProps, **kwargs):
        # Only pass scope and id to the Construct base class
        super().__init__(scope, id)

        version_id = f'Version{hash_code(props)}'
        self.props = props

        # Store parameters as instance variables
        self.region = Stack.of(scope).region
        self.account = Stack.of(scope).account

        # Create or use provided role
        self.role = props.role or LexRole(
            self,
            'Role',
            props=LexRoleProps(
                lex_log_group_name=props.log_group.log_group_name
                if props.log_group
                else None
            ),
        )

        # Create bot
        self.bot = CfnBot(
            self,
            'Bot',
            name=props.name[:50],  # Trim to 50 characters
            description=props.description,
            idle_session_ttl_in_seconds=props.idle_session_ttl_in_seconds,
            role_arn=self.role.role_arn,
            data_privacy={'ChildDirected': False},
            bot_locales=[
                l.to_cdk_locale(props.nlu_confidence_threshold) for l in props.locales
            ],
            auto_build_bot_locales=True,  # Turned off to prevent build issues
            test_bot_alias_settings=CfnBot.TestBotAliasSettingsProperty(
                bot_alias_locale_settings=[
                    locale.to_cdk_bot_locale_setting() for locale in props.locales
                ],
                # conversation_log_settings=self.conversation_log_settings('TestBotAlias')
            ),
            # Add the required tag for Connect permissions
            bot_tags=[CfnTag(key='AmazonConnectEnabled', value='True')],
        )

        # Create version with hash to ensure updates
        self.version = CfnBotVersion(
            self,
            version_id,
            bot_id=self.bot.attr_id,
            bot_version_locale_specification=[
                CfnBotVersion.BotVersionLocaleSpecificationProperty(
                    locale_id=locale.locale_id,
                    bot_version_locale_details=CfnBotVersion.BotVersionLocaleDetailsProperty(
                        source_bot_version='DRAFT'
                    ),
                )
                for locale in props.locales
            ],
        )

        # Create alias
        self.alias = CfnBotAlias(
            self,
            'Alias',
            bot_alias_name='live',
            bot_id=self.bot.attr_id,
            bot_alias_locale_settings=[
                locale.to_cdk_bot_alias_locale_setting() for locale in props.locales
            ],
            bot_version=self.version.attr_bot_version,
            conversation_log_settings=self.conversation_log_settings('live'),
        )

        # Add permissions for lambdas
        for locale in props.locales:
            if locale.code_hook and locale.code_hook.lambda_:
                locale.code_hook.lambda_.add_permission(
                    f'lex-lambda-invoke-{locale.locale_id}',
                    principal=iam.ServicePrincipal('lexv2.amazonaws.com'),
                    action='lambda:InvokeFunction',
                    source_arn=f'arn:aws:lex:{self.region}:{self.account}:bot/{self.bot.attr_id}/*/*',
                )
                locale.code_hook.lambda_.add_permission(
                    f'lex-lambda-invoke-{locale.locale_id}-alias',
                    principal=iam.ServicePrincipal('lexv2.amazonaws.com'),
                    action='lambda:InvokeFunction',
                    source_arn=f'arn:aws:lex:{self.region}:{self.account}:bot-alias/{self.bot.attr_id}/*',
                )

        # Associate with connect if provided
        if props.connect_instance_arn:
            # This adds permissions for Connect to invoke Lambda functions
            for locale in props.locales:
                if locale.code_hook and locale.code_hook.lambda_:
                    locale.code_hook.lambda_.add_permission(
                        f'connect-lambda-invoke-{locale.locale_id}',
                        principal=iam.ServicePrincipal('connect.amazonaws.com'),
                        action='lambda:InvokeFunction',
                        source_arn=f'arn:aws:connect:{self.region}:{self.account}:instance/*',
                    )

            AssociateLexBot(
                self,
                'Association',
                connect_instance_arn=props.connect_instance_arn,
                alias=self.alias,
            )

    # Rest of the class remains unchanged
    def _transform_slot_type(self, slot_type: dict) -> dict:
        """Transform slot type dictionary to Lex format"""
        return {
            'name': slot_type.get('name'),
            'description': slot_type.get('description'),
            'slot_type_name': slot_type.get('name'),
            'external_source_setting': {
                'grammar_slot_type_setting': {'source': slot_type.get('grammar_source')}
            }
            if slot_type.get('grammar_source')
            else None,
            'slot_type_values': [
                {'sample_value': {'value': v}} for v in slot_type.get('values', [])
            ],
            'value_selection_setting': {
                'resolution_strategy': slot_type.get(
                    'resolution_strategy', 'OriginalValue'
                )
            },
        }

    def conversation_log_settings(
        self, alias_name: str
    ) -> Optional[CfnBotAlias.ConversationLogSettingsProperty]:
        """Return conversation log settings"""

        log_group = self.props.log_group
        audio_bucket = self.props.audio_bucket

        # Return None if neither log group nor audio bucket exists
        if not log_group and not audio_bucket:
            return None

        audio_setting: CfnBotAlias.AudioLogSettingProperty = None
        log_settings: CfnBotAlias.TextLogSettingProperty = None

        # Add audio log settings if audio bucket exists
        if audio_bucket:
            audio_setting = [
                CfnBotAlias.AudioLogSettingProperty(
                    enabled=True,
                    destination=CfnBotAlias.AudioLogDestinationProperty(
                        s3_bucket=CfnBotAlias.S3BucketLogDestinationProperty(
                            s3_bucket_arn=audio_bucket.bucket_arn,
                            log_prefix=f'{self.props.name}/{alias_name}',
                            # "kmsKeyArn": "todo"
                        )
                    ),
                )
            ]

        # Add text log settings if log group exists
        if log_group:
            log_settings = [
                CfnBotAlias.TextLogSettingProperty(
                    enabled=True,
                    destination=CfnBotAlias.TextLogDestinationProperty(
                        cloud_watch=CfnBotAlias.CloudWatchLogGroupLogDestinationProperty(
                            cloud_watch_log_group_arn=log_group.log_group_arn,
                            log_prefix=f'{self.props.name}/{alias_name}',
                        )
                    ),
                )
            ]

        return CfnBotAlias.ConversationLogSettingsProperty(
            audio_log_settings=audio_setting,
            text_log_settings=log_settings,
        )
