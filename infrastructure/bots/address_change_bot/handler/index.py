import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event: Dict[str, Any], context=None):
    """
    Handler for address change Lambda fulfillment
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

    if intent_name != 'AddressChange':
        return failed_response(
            f"Lambda doesn't know how to handle intent: {intent_name}"
        )

    house_number = get_slot('houseNumber')
    street_name = get_slot('streetName')
    city = get_slot('city')
    state = get_slot('state')
    zip_code = get_slot('zipCode')

    # TODO: Validate address & Update DB?
    logger.debug(
        'Address result: house_number=%s, street_name=%s, city=%s, state=%s, zip_code=%s',
        house_number,
        street_name,
        city,
        state,
        zip_code,
    )

    # Since we can't use await in Python synchronously, we'll simulate with a simple value
    is_success = True  # await Promise.resolve(true) in TypeScript

    return (
        fulfilled_response('Success')
        if is_success
        else failed_response('Validation or DB Update failed')
    )
