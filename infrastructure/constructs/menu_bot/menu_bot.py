import json
import os
from typing import List, Optional

from attr import asdict
from aws_cdk import aws_connect as connect
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from ...utils.create_lambda import create_lambda
from ...utils.load_flow_content import load_flow_content
from ..bot_props import BotProps
from ..simple_bot import CodeHook, SimpleBot, SimpleBotProps, SimpleIntent, SimpleLocale
from .models import MenuAction, MenuLocale, TransferAction


def convert_to_lambda_config(locales: List[MenuLocale]) -> str:
    """
    Convert menu locales to a configuration format for the Lambda function

    Args:
        locales: List of MenuLocale objects defining the bot configuration

    Returns:
        A dictionary configuration for the Lambda function
    """
    config = {}
    for locale in locales:
        config[locale.locale_id] = {
            'langCode': locale.locale_id,
            'greeting': locale.greeting,
            'morePrompt': locale.more_prompt,
            'help': locale.help.response,
            'hangUp': locale.hang_up.response,
        }

        # Add menu items and their actions
        for key, value in locale.menu.items():
            config[locale.locale_id][key] = asdict(value.action)

    return json.dumps(config)


def unique_custom_handlers(locales: List[MenuLocale]) -> List[str]:
    """
    Extract unique custom handler ARNs from all locales

    Args:
        locales: List of MenuLocale objects

    Returns:
        List of unique custom handler ARNs
    """
    handlers = set()

    for locale in locales:
        for menu_item in locale.menu.values():
            action = menu_item.action
            if hasattr(action, 'custom_handler') and action.custom_handler:
                handlers.add(action.custom_handler)

    return list(handlers)


def fulfillment_prompt(action: MenuAction) -> Optional[str]:
    """
    Fulfillment prompt is played after the intent fulfillment code-hook completes,
    but before the caller is returned to Connect.
    """
    if isinstance(action, TransferAction):
        return action.pre_transfer_prompt
    return None


class MenuBotProps(BotProps):
    """
    Properties for the MenuBot construct
    """

    def __init__(
        self,
        *,
        locales: List[MenuLocale],
        include_module: bool = True,
        include_sample_flow: bool = False,
        **kwargs,
    ):
        # Initialize parent class with kwargs
        super().__init__(**kwargs)

        # Initialize our own properties
        self.locales = locales
        self.include_module = include_module
        self.include_sample_flow = include_sample_flow


class MenuBot(Construct):
    """
    Creates a Lex bot with a menu structure for handling basic customer interactions
    """

    def __init__(self, scope: Construct, id: str, *, props: MenuBotProps, **kwargs):
        # First, initialize the Construct base class with just scope and id
        super().__init__(scope, id)

        prefix = props.prefix
        menu_locales = props.locales
        connect_instance_arn = props.connect_instance_arn
        include_module = props.include_module
        include_sample_flow = props.include_sample_flow

        bot_name = f'{prefix}-{id}'
        config_json = convert_to_lambda_config(menu_locales)

        # Create Lex handler
        self.lex_handler = create_lambda(
            self,
            'LexHandler',
            os.path.join(os.path.dirname(__file__), 'lambdas', 'lex_handler'),
            function_name=f'{bot_name}-lex-handler',
            description=f'Manages the {bot_name} lex conversation',
            environment={'CONFIG': config_json},
        )

        # Allow lex handler to invoke custom action lambdas
        for i, handler in enumerate(unique_custom_handlers(menu_locales)):
            imported = lambda_.Function.from_function_attributes(
                self,
                f'CustomHandlerImport{i}',
                function_arn=handler,
                same_environment=True,
            )
            imported.grant_invoke(self.lex_handler)

        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id=locale.locale_id,
                voice_id=locale.voice_id,
                code_hook=CodeHook(
                    lambda_=self.lex_handler,
                    fulfillment=True,
                    dialog=True,
                ),
                intents=[
                    SimpleIntent(
                        name='help',
                        utterances=locale.help.utterances,
                    ),
                    SimpleIntent(
                        name='hangUp',
                        utterances=locale.hang_up.utterances,
                    ),
                    # Add intents from the menu
                    *[
                        SimpleIntent(
                            name=key,
                            utterances=value.utterances,
                            confirmation_prompt=value.confirmation,
                            fulfillment_prompt=fulfillment_prompt(value.action),
                        )
                        for key, value in locale.menu.items()
                    ],
                ],
            )
            for locale in menu_locales
        ]

        # Create the bot
        self.bot = SimpleBot(
            self,
            'Bot',
            props=SimpleBotProps(
                name=bot_name,
                prefix=props.prefix,
                description=props.description,
                role=props.role,
                idle_session_ttl_in_seconds=props.idle_session_ttl_in_seconds,
                nlu_confidence_threshold=props.nlu_confidence_threshold,
                log_group=props.log_group,
                audio_bucket=props.audio_bucket,
                connect_instance_arn=connect_instance_arn,
                locales=locales,
            ),
        )

        # Create Connect handler Lambda
        connect_handler = create_lambda(
            self,
            'ConnectHandler',
            os.path.join(os.path.dirname(__file__), 'lambdas', 'connect_handler'),
            function_name=f'{bot_name}-connect-handler',
            description='Provides greeting information to Connect. Expects a lang parameter.',
            environment={'CONFIG': config_json},
        )

        # Connect has a limited number of associations, since this is system lambda,
        # we give connect permissions to invoke, but we dont show it in the flow designer
        connect_handler.add_permission(
            'ConnectInvoke',
            principal=iam.ServicePrincipal('connect.amazonaws.com'),
            action='lambda:InvokeFunction',
            source_arn=connect_instance_arn,
        )

        # Optionally create Connect module and sample flow
        if include_module:
            module_content = load_flow_content(
                os.path.join(os.path.dirname(__file__), 'Module.json'),
                {
                    'BotArn': self.bot.alias.attr_arn,
                    'LambdaArn': connect_handler.function_arn,
                },
            )

            module = connect.CfnContactFlowModule(
                self,
                'ConnectModule',
                instance_arn=connect_instance_arn,
                name=f'{bot_name} Module',
                description=f'Handles interactions with the {bot_name} Lex bot',
                content=module_content,
            )

            if include_sample_flow:
                default_locale = menu_locales[0]
                flow_content = load_flow_content(
                    os.path.join(os.path.dirname(__file__), 'SampleFlow.json'),
                    {
                        'ModuleId': module.ref,
                        'Voice': default_locale.voice_id,
                        'Lang': default_locale.locale_id,
                    },
                )

                connect.CfnContactFlow(
                    self,
                    'ConnectFlow',
                    instance_arn=connect_instance_arn,
                    type='CONTACT_FLOW',
                    name=f'{bot_name} Flow',
                    description=f'Handles interactions with the {bot_name} Lex bot',
                    content=flow_content,
                )
