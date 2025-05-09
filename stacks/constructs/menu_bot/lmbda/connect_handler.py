import json
import logging
import os
from typing import Dict, Any, Optional
from .interface import LambdaConfig
from ....utils.logger import logger
from ....utils.get_env_var import parse_env_var

# Type annotations for Connect event
class ConnectEvent:
    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self.details = event.get('Details', {})
        self.parameters = self.details.get('Parameters', {})
        self.contact_data = self.details.get('ContactData', {})
        self.language_code = self.contact_data.get('LanguageCode', '')

class ConnectHandler:
    def __init__(self, config: LambdaConfig):
        self.config = config

    @classmethod
    def create(cls):
        try:
            return cls(parse_env_var('CONFIG'))
        except ValueError:
            # During CDK synth or when environment variables aren't available,
            # return a default configuration to allow synth to proceed
            default_config = {
                "en_US": {
                    "greeting": "Default greeting",
                    "more_prompt": "Default prompt",
                    "help": "Default help",
                    "hang_up": "Default hang up message"
                }
            }
            return cls(default_config)

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, str]:
        """
        Handle Amazon Connect contact flow events
        """
        try:
            connect_event = ConnectEvent(event)

            # Get language from parameters or contact data, default to en_US
            lang_param = connect_event.parameters.get('lang', None)
            lang_code = connect_event.language_code

            # Default to en_US and replace hyphens with underscores
            lang = (lang_param or lang_code or 'en_US').replace('-', '_')

            # Get locale config
            locale_config = self.config.get(lang, {})

            # Construct response
            response = {
                'greeting': locale_config.get('greeting', ''),
                'morePrompt': locale_config.get('more_prompt', ''),
                'help': locale_config.get('help', ''),
                'hangUp': locale_config.get('hang_up', '')
            }

            logger.debug('result', {'response': response})
            return response

        except Exception as error:
            logger.error('Unhandled Error', {'error': str(error)})
            raise

# Create handler instance
handler_class = ConnectHandler.create()

def handler(event, context):
    """
    AWS Lambda handler function
    """
    return handler_class.handler(event, context)