import os
import json
from typing import Any, TypeVar, Generic

T = TypeVar('T')

def get_env_var(name: str, default_val: str = '') -> str:
    """
    Access environment variable and throw error if it is undefined
    """
    val = os.environ.get(name, default_val)

    if not val:
        raise ValueError(f"Environment parameter {name} is undefined")
    return val

def parse_env_var(name: str, type_hint: Any = None) -> Any:
    """
    Access a JSON object from an environment variable
    """
    json_str = get_env_var(name)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        raise ValueError(f"Environment variable {name} is not valid JSON")
