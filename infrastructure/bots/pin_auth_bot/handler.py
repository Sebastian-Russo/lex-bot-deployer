import json
from typing import Dict, Any
from lex_project_template_py.lambda_shared.lex_helper import LexHelper
from lex_project_template_py.utils.logger import logger

def handler(event: Dict[str, Any], context=None) -> Dict[str, Any]:
    """
    Handler for PIN authentication Lambda

    TODO - Do not log accountId and accountPin in production.
    """
    if event.get('invocationSource') != 'FulfillmentCodeHook':
        raise Exception(f"{event.get('invocationSource')} is not implemented yet")

    helper = LexHelper(event)

    if helper.intent_name != 'AccountNumber':
        return helper.failed_response(f"Lambda doesnt know how to handle intent: {helper.intent_name}")

    account_id = helper.slot_value('accountId')
    account_pin = helper.slot_value('accountPin')

    if not account_id:
        raise Exception('accountId is blank')
    if not account_pin:
        raise Exception('accountPin is blank')

    # TODO: Check DB to verify PIN?
    logger.debug('result', {'accountId': account_id, 'accountPin': account_pin})
    # Since we can't use await in Python synchronously, we'll simulate this with a simple value
    is_valid = False  # await Promise.resolve(false) in TypeScript

    return helper.fulfilled_response('Success') if is_valid else helper.failed_response('Invalid PIN')