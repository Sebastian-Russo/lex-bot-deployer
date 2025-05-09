import json
import logging
from typing import Dict, Optional, Any, Union, Literal
import boto3
from botocore.exceptions import ClientError

from .interface import LambdaConfig
from ....lambda_shared import LexHelper
from ....utils import parse_env_var
from ..models import MenuAction

# Configure logging
logger = logging.getLogger(__name__)

class Attributes:
    """
    Attributes for the Lex session
    """
    def __init__(self):
        """
        Which action is associated with the intent
        """
        self.action: str = ""

        """
        Where to transfer the call
        """
        self.destination: str = ""

        """
        Call should hang up after bot returns
        """
        self.hang_up: Literal["true", "false"] = "false"

class LexHandler:
    def __init__(self, config: LambdaConfig, lambda_client=None):
        self.config = config
        self.lambda_client = lambda_client or boto3.client('lambda')
        self.event = None
        self.helper = None

    @classmethod
    def create(cls):
        return cls(parse_env_var('CONFIG'), boto3.client('lambda'))

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        logger.info('event: %s', event)
        self.event = event
        self.helper = LexHelper(event)

        try:
            if event.get('invocationSource') == 'DialogCodeHook':
                return self.dialog_hook()
            elif event.get('invocationSource') == 'FulfillmentCodeHook':
                return self.fulfillment_hook()
            else:
                raise ValueError(f"Unknown invocation source {event.get('invocationSource')}")
        except Exception as error:
            logger.error('Unhandled Error: %s', str(error))
            return self.helper.failed_response('Unhandled lambda error')

    def dialog_hook(self) -> Dict[str, Any]:
        helper = self.helper
        intent = helper.event['sessionState']['intent']
        state = intent.get('state')
        confirmation_state = intent.get('confirmationState')

        if state == 'InProgress' and confirmation_state == 'Denied':
            locale = self.config[helper.locale_id]
            # User denied confirmation
            return helper.elicit_intent(locale.get('more_prompt', ''))
        else:
            return helper.delegate()

    def fulfillment_hook(self) -> Dict[str, Any]:
        helper = self.helper
        locale_id = helper.locale_id
        intent_name = helper.intent_name

        locale = self.config.get(locale_id)
        if not locale:
            raise ValueError(f"Locale {locale_id} is not configured")

        if intent_name == 'help' or intent_name == 'FallbackIntent':
            return helper.elicit_intent(locale.get('help', ''))
        if intent_name == 'hangUp':
            return helper.fulfilled_response(locale.get('hang_up', ''))
        if intent_name not in locale:
            raise ValueError(f"Intent {intent_name} not found in config")

        action = locale[intent_name]
        if action.get('customHandler'):
            self.custom_handler(action['customHandler'])

        helper.session_attributes['action'] = action.get('type', '')

        if action.get('type') == 'Prompt':
            if action.get('hangUp'):
                helper.session_attributes['hangUp'] = 'true'
                return helper.fulfilled_response(action.get('prompt', ''))
            message = f"{action.get('prompt', '')}... {locale.get('more_prompt', '')}"
            return helper.elicit_intent(message)
        elif action.get('type') == 'PhoneTransfer':
            helper.session_attributes['destination'] = action.get('phoneNumber', '')
            return helper.fulfilled_response()
        elif action.get('type') == 'QueueTransfer':
            helper.session_attributes['destination'] = action.get('queueArn', '')
            return helper.fulfilled_response()
        elif action.get('type') == 'FlowTransfer':
            helper.session_attributes['destination'] = action.get('contactFlowArn', '')
            return helper.fulfilled_response()

        return helper.failed_response(f"Unknown action type: {json.dumps(action, indent=2)}")

    def custom_handler(self, lambda_arn: str) -> None:
        function_name = lambda_arn.split('function/')[-1] if 'function/' in lambda_arn else lambda_arn
        logger.info("Passing event to custom handler: %s", function_name)

        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='Event',
                Payload=json.dumps(self.event)
            )
            logger.info('Lambda invocation response: %s', response)
        except ClientError as e:
            logger.error("Error invoking Lambda function: %s", str(e))


# Create handler instance
handler_class = LexHandler.create()
def handler(event, context):
    return handler_class.handler(event, context)