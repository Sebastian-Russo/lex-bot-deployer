import json
import logging
import os
import random
import re
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class OfficeLocatorHandler:
    """
    Handles the conversation flow for SSA office locator using conditional slots
    """

    def __init__(self):
        self.office_api_endpoint = os.environ.get('OFFICE_API_ENDPOINT')

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        """Route to dialog_hook() or fulfillment_hook()"""
        logger.debug('Event: %s', json.dumps(event, indent=2))

        try:
            invocation_source = event.get('invocationSource')
            if invocation_source == 'DialogCodeHook':
                return self.dialog_hook(event)
            elif invocation_source == 'FulfillmentCodeHook':
                return self.fulfillment_hook(event)
            else:
                raise ValueError(f'Unknown invocation source: {invocation_source}')

        except Exception as e:
            logger.error('Handler error: %s', str(e))
            return self.close_response(
                intent_name='Failed',
                message='I apologize, but I encountered an error. Let me transfer you to an agent.',
                session_attributes=self.get_session_attributes(event),
            )

    def dialog_hook(self, event):
        """Handle dialog hook"""
        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'LocateOffice':
            if not slots.get('zipCode') or not slots['zipCode'].get('value'):
                return self.elicit_slot_response(
                    'zipCode',
                    'Go ahead and say or enter the five digit zip code for your area or the area where you want to find an office.',
                    session_attributes,
                    intent_object,
                )

            zip_code = slots['zipCode']['value']['interpretedValue']

            # P1110e: (In-Hour) I don't know
            if (
                "i don't know" in zip_code.lower()
                or "i don't have it" in zip_code.lower()
                or "i'm not sure" in zip_code.lower()
            ):
                session_attributes.update(
                    {
                        'action': 'TransferToAgent',
                        'reason': 'NoZipCode',
                    }
                )
                return self.close_response(
                    intent_name=intent_name,
                    # P1110e: (In-Hour)
                    message="Sounds like you don't know the zip code. Let me connect you to an agent.",
                    # P1110e: (Off-Hour)
                    # message="Sounds like you don't know the zip code. Normally I'd get an agent to help you, but unfortunately we're closed.",
                    session_attributes=session_attributes,
                )

            # Validate zip code format
            if not re.match(r'^\d{5}$', zip_code):
                intent_object['slots']['zipCode'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    'That zip code is invalid. Please say a five-digit zip code, like 12345.',
                    session_attributes,
                    intent_object,
                )

            # Step 5. Confirm zip code
            if not slots.get('confirmZip') or not slots['confirmZip'].get('value'):
                return self.elicit_slot_response(
                    'confirmZip',
                    # P1118
                    f'That zip code is {zip_code}. Right?',
                    session_attributes,
                    intent_object,
                )
            confirm_zip = slots['confirmZip']['value']['interpretedValue']

            if 'no' in confirm_zip.lower():
                intent_object['slots']['zipCode'] = None
                intent_object['slots']['confirmZip'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    "My mistake. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.",
                    session_attributes,
                    intent_object,
                )

            if 'yes' in confirm_zip.lower() or 'right' in confirm_zip.lower():
                # Step 6. Ask about card needs
                if not slots.get('needsCard') or not slots['needsCard'].get('value'):
                    return self.elicit_slot_response(
                        'needsCard',
                        'Thanks. Do you need to get a Social Security card?',
                        session_attributes,
                        intent_object,
                    )

            return self.fulfillment_hook(event)

        if intent_name == 'Finished':
            return self.close_response(
                intent_name=intent_name,
                message='Ok, finished. Have a nice day.',
                session_attributes=session_attributes,
            )

        if intent_name == 'ReturnToMenu':
            return self.close_response(
                intent_name=intent_name,
                message='Returning to the main menu.',
                session_attributes=session_attributes,
            )

        # Fallback for unexpected intents
        return self.close_response(
            intent_name=intent_name,
            message="Sorry, I didn't understand. Please say 'office' to locate an offic.",
            session_attributes=session_attributes,
        )

    def fulfillment_hook(self, event):
        """Handle fulfillment for office locator intent"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)
        intent_object = event['sessionState']['intent']

        if intent_name == 'LocateOffice':
            # Extract user data
            zip_code = (
                slots['zipCode']['value']['interpretedValue']
                if slots.get('zipCode') and slots['zipCode'].get('value')
                else session_attributes.get('zipCode')
            )
            needs_card = (
                slots['needsCard']['value']['interpretedValue'].lower()
                if slots.get('needsCard') and slots['needsCard'].get('value')
                else session_attributes.get('needsCard', 'no').lower()
            )

            # Mock API call to check if Card Center exists (and retrieve office info)
            def card_center_in_zip_result(zip_code):
                result = random.choice([True, True, True, True, True, False])
                response_success = {
                    'status': 'success',
                    'office_hours': '9am - 5pm',
                    'office_phone': '867-5309',
                    'office_name': 'Social Security Administration',
                    'office_address': '123 Main St',
                    'office_city': 'Springfield',
                    'office_state': 'CO',
                    'office_zip': zip_code,
                }
                response_failure = {'status': 'failure'}
                return response_success if result else response_failure

            api_response = card_center_in_zip_result(zip_code)

            if api_response.get('status') == 'failure':
                intent_object['slots']['confirmZip'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    # P1110C
                    "That is an invalid Zip Code. Let's try again. Please say the live digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.",
                    session_attributes,
                    intent_object,
                )
            if api_response.get('status') == 'success':
                address = api_response['office_address']
                hours = api_response['office_hours']
                phone = api_response['office_phone']
                if needs_card == 'yes':
                    # message P1122 andP1123
                    return self.close_response(
                        session_attributes=session_attributes,
                        intent_name=intent_name,
                        message=f'All right. To apply for a new or replacement Social Security card, you will need to visit the card center in your area which is located at {address}. The hours of operation are, {hours}. To hear that again, say repeat that.'
                        + "For information about the local Social Security office, say local office. To search in a different zip code, say change zip code. Or if you're finished, just say, I'm finished.",
                    )
                # message P1112 and P1113
                if needs_card == 'no':
                    return self.close_response(
                        session_attributes=session_attributes,
                        intent_name=intent_name,
                        message=f"Okay, here's information for the servicing office in the zip code {zip_code}. The address is {address}. The hours of operation are {hours}. And the phone number is {phone}."
                        + "To hear that again, say repeat that. Otherwise, to search in a different zip code, say change zip code. Or if you're finished, just say, I'm finished.",
                    )

        # Fallback for unexpected intents
        return self.close_response(
            session_attributes=session_attributes,
            intent_name=intent_name,
            message='An error occurred.',
        )

    ### Helper functions to extra data ###
    def get_intent_name(self, event):
        """Extract intent name from event"""
        return event.get('sessionState', {}).get('intent', {}).get('name', '')

    def get_slots(self, event):
        """Extract slots from event"""
        return event.get('sessionState', {}).get('intent', {}).get('slots', {})

    def get_session_attributes(self, event):
        """Extract session attributes from event"""
        return event.get('sessionState', {}).get('sessionAttributes', {})

    ### Helper functions to build Lex responses ###

    def elicit_slot_response(self, slot_name, message, session_attributes, intent):
        """Build "ask for slot" response"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_name},
                'intent': intent,
                'sessionAttributes': session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def delegate_response(self, session_attributes, intent_object):
        """Build "let Lex continue" response"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'Delegate'},
                'intent': intent_object,
                'sessionAttributes': session_attributes,
            },
        }

    def close_response(self, session_attributes, intent_name, message):
        """Build "conversation finished" response"""
        response = {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled',  # or 'Failed'
                },
                'sessionAttributes': session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

        # Test code for Lex Fulfillment Handler
        if session_attributes.get('test-case'):
            response_string = response.get('messages', [{}])[0].get(
                'content', '[no Response>'
            )
            expected_response = session_attributes.get('expected_response')
            expected_intent = session_attributes.get('expected_intent')

            def is_equal(str1: str, str2: str) -> bool:
                """
                Compares two strings while ignoring case, leading/tailing whitespace, and repeated white spaces.
                """

                def normalize_string(s: str) -> str:
                    if s is None:
                        return ''
                    return ' '.join(s.strip().lower().split())

                return normalize_string(str1) == normalize_string(str2)

            if not is_equal(expected_response, response_string):
                result = 'FAILED'
                session_attributes['test-explanation'] = (
                    f'Expected response = {expected_response}, got {response_string}'
                )

            elif not is_equal(expected_intent, intent_name):
                result = 'FAILED'
                session_attributes['test-explanation'] = (
                    f'Expected intent = {expected_intent}, got {intent_name}'
                )

            else:
                result = 'PASSED'
                session_attributes['test-explanation'] = (
                    'Response and intent match expected values'
                )

            session_attributes['test-result'] = result
            response['sessionState']['sessionAttributes'] = session_attributes

        return response


# Create handler instance
handler_instance = OfficeLocatorHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
