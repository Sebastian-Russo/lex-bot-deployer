import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event):
    logger.debug('Event: %s', json.dumps(event, indent=2))

    parameters = event['Details']['Parameters']
    lang_code = event['Details']['ContactData']['LanguageCode']

    # Get language from parameters, fallback to contact language, then to default 'en_US'
    lang = (parameters.get('lang') or lang_code or 'en_US').replace('-', '_')

    config = json.loads(os.environ['CONFIG'])
    locale = config[lang]

    return {
        'greeting': locale.greeting,
        'morePrompt': locale.morePrompt,
        'help': locale.help,
        'hangUp': locale.hangUp,
    }
