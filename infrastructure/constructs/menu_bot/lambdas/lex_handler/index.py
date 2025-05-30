import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from helper import LexHelper

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))

lambda_client = boto3.client('lambda')


class LexHandler:
    """
    Handles Lex events for menu-based bots
    """

    config = None

    def __init__(self):
        """
        Initialize the handler with configuration from file
        """
        # Read config from file instead of environment variable
        config_file_path = os.path.join(os.path.dirname(__file__), 'menu_config.json')
        try:
            with open(config_file_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise ValueError(f'Config file not found at {config_file_path}')
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON in config file: {str(e)}')

    # def __init__(self):
    #     """
    #     Initialize the handler with configuration from environment variables
    #     """
    #     config_str = os.environ.get('CONFIG')
    #     if not config_str:
    #         raise ValueError('CONFIG environment variable is required but was empty')
    #     self.config = json.loads(config_str)

    #     self.event = None
    #     self.helper = None

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        """
        Main handler function for Lex events
        """
        logger.debug('Event: %s', json.dumps(event, indent=2))
        self.helper = LexHelper(event)

        try:
            invocation_source = event.get('invocationSource')
            if invocation_source == 'DialogCodeHook':
                return self.dialog_hook()
            elif invocation_source == 'FulfillmentCodeHook':
                return self.fulfillment_hook()
            else:
                raise ValueError(f'Unknown invocation source {invocation_source}')
        except Exception as e:
            logger.error(f'Unhandled Error: {str(e)}')
            return self.helper.failed_response('Unhandled lambda error')

    def dialog_hook(self) -> Dict[str, Any]:
        """
        Handle dialog code hook invocations
        """
        helper = self.helper
        intent = helper.event['sessionState']['intent']
        state = intent.get('state')
        confirmation_state = intent.get('confirmationState')

        if state == 'InProgress' and confirmation_state == 'Denied':
            locale = self.config.get(helper.locale_id, {})
            # User denied confirmation
            return helper.elicit_intent(
                locale.get('morePrompt', 'Is there anything else I can help you with?')
            )
        else:
            return helper.delegate()

    def fulfillment_hook(self) -> Dict[str, Any]:
        """
        Handle fulfillment code hook invocations
        """
        helper = self.helper
        locale_id = helper.locale_id
        intent_name = helper.intent_name

        locale = self.config.get(locale_id)
        if not locale:
            raise ValueError(f'Locale {locale_id} is not configured')

        if intent_name == 'help' or intent_name == 'FallbackIntent':
            return helper.elicit_intent(locale.get('help', ''))
        if intent_name == 'hangUp':
            return helper.fulfilled_response(locale.get('hangUp', ''))
        if intent_name not in locale:
            raise ValueError(f'Intent {intent_name} not found in config')

        action = locale[intent_name]
        if action.get('customHandler'):
            self.custom_handler(action['customHandler'])

        helper.session_attributes['action'] = action.get('type', '')

        if action.get('type') == 'Prompt':
            if action.get('hang_up'):
                helper.session_attributes['hangUp'] = 'true'
                return helper.fulfilled_response(action.get('prompt', ''))
            message = f'{action.get("prompt", "")}... {locale.get("more_prompt", "")}'
            return helper.elicit_intent(message)
        elif action.get('type') == 'PhoneTransfer':
            helper.session_attributes['destination'] = action.get('phone_number', '')
            return helper.fulfilled_response(action.get('pre_transfer_prompt'))
        elif action.get('type') == 'QueueTransfer':
            helper.session_attributes['destination'] = action.get('queue_arn', '')
            return helper.fulfilled_response(action.get('pre_transfer_prompt'))
        elif action.get('type') == 'FlowTransfer':
            helper.session_attributes['destination'] = action.get(
                'contact_flow_arn', ''
            )
            return helper.fulfilled_response(action.get('pre_transfer_prompt'))

        return helper.failed_response(
            f'Unknown action type: {json.dumps(action, indent=2)}'
        )

    def custom_handler(self, lambda_arn: str) -> None:
        """
        Invoke a custom handler Lambda function
        """
        function_name = (
            lambda_arn.split('function/')[-1]
            if 'function/' in lambda_arn
            else lambda_arn
        )
        logger.info(f'Passing event to custom handler: {function_name}')

        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='Event',
                Payload=json.dumps(self.event),
            )
            logger.info(f'Lambda invocation response: {response}')
        except ClientError as e:
            logger.error(f'Error invoking Lambda function: {str(e)}')


# Create handler instance
handler_instance = LexHandler()


def handler(event, context=None):
    """
    Lambda handler function
    """
    return handler_instance.handler(event, context)
