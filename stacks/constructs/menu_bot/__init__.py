"""
Lambda function implementations for the MenuBot construct.
"""

# Try to import the handlers, with fallbacks for synthesis time
try:
    from .connect_handler import handler as connect_handler
except ImportError as e:
    # Provide a dummy handler for CDK synthesis
    print(f"Warning: Could not import connect_handler for CDK synthesis: {e}")
    def connect_handler(*args, **kwargs):
        pass

try:
    from .lex_handler import handler as lex_handler
except ImportError as e:
    # Provide a dummy handler for CDK synthesis
    print(f"Warning: Could not import lex_handler for CDK synthesis: {e}")
    def lex_handler(*args, **kwargs):
        pass

# Export other important components needed during CDK synthesis
try:
    from .interface import convert_to_lambda_config, unique_custom_handlers, LambdaConfig
except ImportError as e:
    print(f"Warning: Could not import interface components for CDK synthesis: {e}")
    # You might need to define minimal versions of these if they're used during synthesis