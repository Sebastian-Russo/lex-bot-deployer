# In stacks/lmbda/l2_constructs/menu_bot/__init__.py
try:
    from .routing.lex_handler import handler as lex_handler
    from .routing.interface import LambdaConfig, convert_to_lambda_config
    from .connect_handler import handler as connect_handler
except ImportError:
    # Dummy implementations for synthesis
    def convert_to_lambda_config(locales):
        return {}

    def unique_custom_handlers(locales):
        return []