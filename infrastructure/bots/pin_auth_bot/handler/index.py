import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event: Dict[str, Any], context=None):
    """
    Handler for PIN authentication Lambda

    TODO - Do not log accountId and accountPin in production.
    """

    logger.debug('Event: %s', json.dumps(event, indent=2))

    if event['invocationSource'] != 'FulfillmentCodeHook':
        raise Exception(f'{event["invocationSource"]} is not implemented yet')

    session_attributes = event['sessionState']['sessionAttributes']
    interpretation = event['interpretations'][0]
    intent = interpretation['intent']
    intent_name = intent['name']
    slots = intent['slots']

    def get_slot(name):
        return slots[name]['value']['interpretedValue']

    def failed_response(message: str):
        return {
            'sessionState': {
                'sessionAttributes': session_attributes,
                'dialogAction': {'type': 'Close'},
                'intent': {'slots': slots, 'name': intent_name, 'state': 'Failed'},
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def fulfilled_response(message: str = None) -> Dict[str, Any]:
        result = {
            'sessionState': {
                'sessionAttributes': session_attributes,
                'dialogAction': {'type': 'Close'},
                'intent': {'slots': slots, 'name': intent_name, 'state': 'Fulfilled'},
            }
        }

        if message:
            result['messages'] = [{'contentType': 'PlainText', 'content': message}]

        return result

    if intent_name != 'AccountNumber':
        return failed_response(
            f'Lambda doesnt know how to handle intent: {intent_name}'
        )

    account_id = get_slot('accountId')
    account_pin = get_slot('accountPin')

    if not account_id:
        raise Exception('accountId is blank')
    if not account_pin:
        raise Exception('accountPin is blank')

    # TODO: Check DB to verify PIN?
    logger.debug('result', {'accountId': account_id, 'accountPin': account_pin})

    # Since we can't use await in Python synchronously, we'll simulate this with a simple value
    is_valid = False  # TODO: Validate the PIN

    return fulfilled_response('Success') if is_valid else failed_response('Invalid PIN')
