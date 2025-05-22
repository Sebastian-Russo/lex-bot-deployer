import json
from aws_cdk import Token
from constructs import Construct
import dataclasses

def safe_stringify(obj):
    """
    Stringify object which excludes constructs (circular reference)

    Args:
        obj: The object to stringify

    Returns:
        JSON string representation of the object
    """
    def replacer(val):
        """Function for handling non-serializable objects"""
        if isinstance(val, Construct):
            # Don't serialize constructs
            return f"construct-{val.node.id}"

        if callable(val):
            # Don't serialize functions
            return "{function}"

        if isinstance(val, str) and Token.is_unresolved(val):
            # Don't serialize unresolved tokens.
            # Token change with each synth, which breaks the hashing operation
            return "{token}"

        if dataclasses.is_dataclass(val):
            dict = dataclasses.asdict(val)
            for key, value in dict.items():
                dict[key] = replacer(value)
            return dict

        if isinstance(val, list):
            return json.dumps(val, default=replacer)

        # For any other non-serializable objects
        return str(val)

    # Use only the default replacer function approach
    return json.dumps(obj, default=replacer)