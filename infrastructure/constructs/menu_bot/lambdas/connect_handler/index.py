import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event, context=None):
    logger.debug('Event: %s', json.dumps(event, indent=2))

    parameters = event.get('Details', {}).get('Parameters', {})
    lang_code = event.get('Details', {}).get('ContactData', {}).get('LanguageCode')

    # Get language from parameters, fallback to contact language, then to default 'en_US'
    lang = (parameters.get('lang') or lang_code or 'en_US').replace('-', '_')

    config_str = os.environ.get('CONFIG')
    if not config_str:
        raise ValueError('CONFIG environment variable is required but was empty')

    config = json.loads(config_str)
    locale = config.get(lang, {})

    return {
        'greeting': locale.get('greeting', ''),
        'morePrompt': locale.get('morePrompt', ''),
        'help': locale.get('help', ''),
        'hangUp': locale.get('hangUp', ''),
    }
