# __init__.py
from .get_env_var import get_env_var, parse_env_var


# Make these functions available when importing the package
__all__ = ['get_env_var', 'parse_env_var']
