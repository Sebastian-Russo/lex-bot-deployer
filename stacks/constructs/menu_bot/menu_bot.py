import os
import json
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_connect as connect
from .lmbda.interface import convert_to_lambda_config, unique_custom_handlers
from ..simple_bot import SimpleBot
from ..bot_props import BotProps
from .models import MenuLocale
from ...utils.load_flow_content import load_flow_content
from typing import List, Optional, Dict, Any

def fulfillment_prompt(action: Dict[str, Any]) -> Optional[str]:
    """
    Fulfillment prompt is played after the intent fulfillment code-hook completes,
    but before the caller is returned to Connect.
    """
    if action.get('pre_transfer_prompt') and isinstance(action.get('pre_transfer_prompt'), str):
        return action.get('pre_transfer_prompt')
    return None

class MenuBotProps(BotProps):
    """
    Properties for the MenuBot construct
    """
    def __init__(
        self,
        *,
        locales: List[MenuLocale],
        logging_level: str = 'debug',
        include_module: bool = True,
        include_sample_flow: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.locales = locales
        self.logging_level = logging_level
        self.include_module = include_module
        self.include_sample_flow = include_sample_flow

class MenuBot(Construct):
    """
    Creates a Lex bot with a menu structure for handling basic customer interactions
    """
    def __init__(self, scope: Construct, id: str, **kwargs):
        # First, initialize the Construct base class with just scope and id
        super().__init__(scope, id)

        # Then create props object with the additional parameters
        props = MenuBotProps(**kwargs)

        prefix = props.prefix
        locales = props.locales
        connect_instance_arn = props.connect_instance_arn
        logging_level = props.logging_level
        include_module = props.include_module
        include_sample_flow = props.include_sample_flow

        bot_name = f"{prefix}-{id}"
        config = convert_to_lambda_config(locales)

        # Create Lex handler Lambda
        self.lex_handler = lambda_.Function(
            self, 'LexHandler',
            function_name=f"{bot_name}-handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='lex_handler.handler',
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), 'lmbda')),
            environment={
                'LOGGING_LEVEL': logging_level,
                'CONFIG': json.dumps(config)
            },
            description=f"Manages the {bot_name} lex conversation"
        )

        # Allow lex handler to invoke custom action lambdas
        custom_handlers = unique_custom_handlers(locales)
        for i, handler in enumerate(custom_handlers):
            imported = lambda_.Function.from_function_attributes(
                self, f"CustomHandlerImport{i}",
                function_arn=handler,
                same_environment=True
            )
            imported.grant_invoke(self.lex_handler)

        # Create the bot
        self.bot = SimpleBot(
            self, 'Bot',
            name=bot_name,
            prefix=props.prefix,
            description=props.description,
            role=props.role,
            idle_session_ttl_in_seconds=props.idle_session_ttl_in_seconds,
            nlu_confidence_threshold=props.nlu_confidence_threshold,
            log_group=props.log_group,
            audio_bucket=props.audio_bucket,
            connect_instance_arn=connect_instance_arn,
            locales=[{
                "locale_id": locale["locale_id"],
                "voice_id": locale["voice_id"],
                "code_hook": {
                    "lambda_": self.lex_handler,
                    "fulfillment": True,
                    "dialog": True
                },
                "intents": [
                    {"name": "help", "utterances": locale["help"]["utterances"]},
                    {"name": "hangUp", "utterances": locale["hang_up"]["utterances"]},
                    # Add intents from the menu
                    *[{
                        "name": key,
                        "utterances": value["utterances"],
                        "confirmation_prompt": value.get("confirmation"),
                        "fulfillment_prompt": fulfillment_prompt(value["action"])
                    } for key, value in locale["menu"].items()]
                ]
            } for locale in locales]
        )

        # Create Connect handler Lambda
        connect_handler = lambda_.Function(
            self, 'ConnectHandler',
            function_name=f"{bot_name}-info",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='connect_handler.handler',
            code=lambda_.Code.from_asset(os.path.join(os.path.dirname(__file__), 'lmbda')),
            environment={
                'LOGGING_LEVEL': logging_level,
                'CONFIG': json.dumps(config)
            },
            description='Provides greeting information to Connect. Expects a lang parameter.'
        )

        # Connect has a limited number of associations, since this is system lambda,
        # we give connect permissions to invoke, but we dont show it in the flow designer
        connect_handler.add_permission(
            'ConnectInvoke',
            principal=iam.ServicePrincipal('connect.amazonaws.com'),
            action='lambda:InvokeFunction',
            source_arn=connect_instance_arn
        )

        # Optionally create Connect module and sample flow
        if include_module:
            module_name = f"{id} Menu Module"
            module_content = load_flow_content(
                os.path.join(os.path.dirname(__file__), 'Module.json'),
                {
                    "BotArn": self.bot.alias.attr_arn,
                    "LambdaArn": connect_handler.function_arn
                }
            )

            module = connect.CfnContactFlowModule(
                self, 'ConnectModule',
                instance_arn=connect_instance_arn,
                name=module_name,
                description=f"Handles interactions with the {bot_name} Lex bot",
                content=module_content
            )

            if include_sample_flow:
                default_locale = locales[0]
                flow_content = load_flow_content(
                    os.path.join(os.path.dirname(__file__), 'SampleFlow.json'),
                    {
                        "ModuleId": module.ref,
                        "Voice": default_locale["voice_id"],
                        "Lang": default_locale["locale_id"]
                    }
                )

                connect.CfnContactFlow(
                    self, 'ConnectFlow',
                    instance_arn=connect_instance_arn,
                    type='CONTACT_FLOW',
                    name=f"{module_name} Sample Flow",
                    description=f"Demonstrates how to use the {module_name}",
                    content=flow_content
                )