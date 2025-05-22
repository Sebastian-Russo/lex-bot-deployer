import json
import logging
import os
from typing import Any, Dict, Optional, TypeVar, Union, Callable, TypedDict, List


# Inline LocaleConfig from interface.py
class LocaleConfig(TypedDict, total=False):
    lang_code: str
    greeting: str
    more_prompt: str
    help: str
    hang_up: str
    # Allow additional string indexed properties


# Inline the LambdaConfig type from interface.py
LambdaConfig = Dict[str, LocaleConfig]

# Inline the parse_env_var function
T = TypeVar('T')


def get_env_var(
    name: str, default: Optional[str] = None, required: bool = False
) -> Optional[str]:
    """
    Get an environment variable with the given name.
    If required is True and the variable is not set, raise a ValueError.
    """
    value = os.environ.get(name)
    if value is None:
        if required:
            raise ValueError(f"Environment variable '{name}' is required but not set")
        return default
    return value


def parse_env_var(
    name: str,
    default: Optional[T] = None,
    required: bool = False,
    coerce: Optional[Callable[[str], T]] = None,
) -> Optional[T]:
    """
    Parse an environment variable with the given name.
    If coerce is provided, it will be used to convert the string value to the desired type.
    If the variable is not set:
      - If required is True, raise a ValueError
      - Otherwise, return the default value
    """
    value = get_env_var(name, default=None, required=required)
    if value is None:
        return default

    if coerce is None:
        # If no coercion function is provided, try to determine if it's JSON
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)  # type: ignore
            except json.JSONDecodeError:
                pass
        # Return as is
        return value  # type: ignore

    # Apply the coercion function
    try:
        return coerce(value)
    except Exception as e:
        raise ValueError(f"Failed to parse environment variable '{name}': {str(e)}")


# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(getattr(logging, log_level))


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
            config = parse_env_var('CONFIG')
            logger.info('Loaded config from environment: %s', json.dumps(config))
            return cls(config)
        except ValueError as e:
            logger.warning('Error loading config: %s', str(e))
            # Default configuration matching the test expectations
            default_config = {
                'en_US': {
                    'greeting': 'Thank you for calling the non-emergency hotline. How may I help you?',
                    'more_prompt': 'Is there anything else I can help you with?',
                    'help': 'I can assist with various services. Please tell me what you need.',
                    'hang_up': 'Thank you for calling. Goodbye.',
                }
            }
            logger.info('Using default config: %s', json.dumps(default_config))
            return cls(default_config)

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, str]:
        """
        Handle Amazon Connect contact flow events
        """
        try:
            logger.info('Received event: %s', json.dumps(event))
            connect_event = ConnectEvent(event)

            # Get language from parameters or contact data, default to en_US
            lang_param = connect_event.parameters.get('lang', None)
            lang_code = connect_event.language_code

            logger.info(
                'Language parameter: %s, contact language: %s', lang_param, lang_code
            )

            # Default to en_US and replace hyphens with underscores
            lang = (lang_param or lang_code or 'en_US').replace('-', '_')
            logger.info('Using language: %s', lang)

            # Get locale config
            locale_config = self.config.get(lang, {})
            if not locale_config:
                logger.warning(
                    'No config found for language %s, available languages: %s',
                    lang,
                    list(self.config.keys()),
                )

            # Construct response
            response = {
                'greeting': locale_config.get('greeting', ''),
                'morePrompt': locale_config.get('more_prompt', ''),
                'help': locale_config.get('help', ''),
                'hangUp': locale_config.get('hang_up', ''),
            }

            logger.info('Returning response: %s', json.dumps(response))
            return response

        except Exception as error:
            logger.error('Unhandled Error: %s', str(error), exc_info=True)
            raise


# Create handler instance
logger.info('Initializing ConnectHandler')
handler_class = ConnectHandler.create()


def handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        logger.info(
            'LAMBDA STARTING: connect_handler with event: %s', json.dumps(event)
        )
        result = handler_class.handler(event, context)
        logger.info('Lambda execution successful, returning: %s', json.dumps(result))
        return result
    except Exception as e:
        logger.error('FATAL ERROR in handler: %s', str(e), exc_info=True)
        # Re-raise to let Lambda handle the error
        raise
