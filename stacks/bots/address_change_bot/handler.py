import json
import logging
from typing import Dict, Any
from ....lambda_shared.lex_helper import LexHelper

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context=None) -> Dict[str, Any]:
    """
    Handler for address change Lambda fulfillment
    """
    if event.get('invocationSource') != 'FulfillmentCodeHook':
        raise Exception(f"{event.get('invocationSource')} is not implemented yet")

    helper = LexHelper(event)

    if helper.intent_name != 'AddressChange':
        return helper.failed_response(f"Lambda doesnt know how to handle intent: {helper.intent_name}")

    house_number = helper.slot_value('houseNumber')
    street_name = helper.slot_value('streetName')
    city = helper.slot_value('city')
    state = helper.slot_value('state')
    zip_code = helper.slot_value('zipCode')

    # TODO: Validate address & Update DB?
    logger.debug('result', {
        'houseNumber': house_number,
        'streetName': street_name,
        'city': city,
        'state': state,
        'zipCode': zip_code
    })

    # Since we can't use await in Python synchronously, we'll simulate with a simple value
    is_success = True  # await Promise.resolve(true) in TypeScript

    return helper.fulfilled_response('Success') if is_success else helper.failed_response('Validation or DB Update failed')