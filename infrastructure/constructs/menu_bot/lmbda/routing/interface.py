from typing import Dict, List, TypedDict
from models import MenuLocale


# Type hint for the Lambda config
class LocaleConfig(TypedDict, total=False):
    lang_code: str
    greeting: str
    more_prompt: str
    help: str
    hang_up: str
    # Allow additional string indexed values that can be MenuAction or string
    # Note: Python's TypedDict doesn't support indexing like TypeScript,
    # so we'd need a runtime check for additional properties


# The main LambdaConfig type
LambdaConfig = Dict[str, LocaleConfig]


def convert_to_lambda_config(locales: List[MenuLocale]) -> LambdaConfig:
    """
    Convert a list of MenuLocale objects to a LambdaConfig dictionary
    """
    config: LambdaConfig = {}
    for locale in locales:
        config[locale['locale_id']] = {
            'lang_code': locale['locale_id'],
            'greeting': locale['greeting'],
            'more_prompt': locale['more_prompt'],
            'help': locale['help']['response'],
            'hang_up': locale['hang_up']['response'],
        }

        # Add menu items
        for key, value in locale['menu'].items():
            config[locale['locale_id']][key] = value['action']

    return config


def unique_custom_handlers(locales: List[MenuLocale]) -> List[str]:
    """
    Reads the menu actions and returns an array of unique custom handlers
    """
    custom_handlers: List[str] = []

    for locale in locales:
        for menu_item in locale['menu'].values():
            custom_handler = menu_item['action'].get('customHandler')
            if custom_handler and custom_handler not in custom_handlers:
                custom_handlers.append(custom_handler)

    return custom_handlers
