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
    def replacer(obj):
        """Function for handling non-serializable objects"""
        if isinstance(obj, Construct):
            # Don't serialize constructs
            return f"construct-{obj.node.id}"

        if callable(obj):
            # Don't serialize functions
            return "{function}"

        if isinstance(obj, str) and Token.is_unresolved(obj):
            # Don't serialize unresolved tokens.
            # Token change with each synth, which breaks the hashing operation
            return "{token}"

        # For any other non-serializable objects
        return str(obj)

    # Use only the default replacer function approach
    return json.dumps(obj, default=replacer, indent=2)