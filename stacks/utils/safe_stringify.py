import json
from aws_cdk import Token
from constructs import Construct

def safe_stringify(obj):
    """
    Stringify object which excludes constructs (circular reference)

    Args:
        obj: The object to stringify

    Returns:
        JSON string representation of the object
    """
    def replacer(key, value):
        if isinstance(value, Construct):
            # Don't serialize constructs
            return f"construct-{value.node.id}"

        if callable(value):
            # Don't serialize functions
            return "{function}"

        if isinstance(value, str) and Token.is_unresolved(value):
            # Don't serialize unresolved tokens.
            # Token change with each synth, which breaks the hashing operation
            return "{token}"

        return value

    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            return replacer(None, obj)

    return json.dumps(obj, cls=CustomEncoder, default=replacer, indent=2)