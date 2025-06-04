import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event, context=None):
    """Lambda handler function"""
    return
