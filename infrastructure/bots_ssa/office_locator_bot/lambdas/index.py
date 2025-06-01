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
            logger.error(f'Handler error: {str(e)}')
            return self.close_response(
                event,
                'Failed',
                'I apologize, but I encountered an error. Let me transfer you to an agent.',
            )

    def dialog_hook(self, event):
        """Handle dialog hook"""
        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'LocateOffice':
            # Step 1. Check if zipCode is set
            if not slots.get('zipCode') or not slots['zipCode'].get('value'):
                return self.elicit_slot_response(
                    'zipCode',
                    'Okay, office information. One moment. Go ahead and say or enter the five digit zip code for your area or the area where you want to find an office.',
                    session_attributes,
                    intent_object,
                )

            zip_code = slots['zipCode']['value']['interpretedValue']

            # Step 2. Check for "change zip code" phrases
            if any(
                phrase in zip_code.lower()
                for phrase in [
                    'change zip code',
                    'different zip code',
                    'new zip code',
                    'search somewhere else',
                    'look somewhere else',
                ]
            ):
                intent_object['slots']['zipCode'] = None
                intent_object['slots']['confirmZip'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    "Alright, let's look somewhere else. Please say the five digit zip code.",
                    session_attributes,
                    intent_object,
                )

            # Step 3. Validate zip code format
            if not re.match(r'^\d{5}$', zip_code):
                return self.elicit_slot_response(
                    'zipCode',
                    "That is an invalid Zip Code. Let's try again. Please say the five digit zip code where you'd like me to search. Like this 1 2 3 0 0. Or enter it on your keypad.",
                    session_attributes,
                    intent_object,
                )

            # Step 4. Check for "I don't know" or "I don't have it"
            if (
                "i don't know" in zip_code.lower()
                or "i don't have it" in zip_code.lower()
            ):
                session_attributes.update(
                    {
                        'action': 'TransferToAgent',
                        'reason': 'NoZipCode',
                    }
                )
                return self.close_response(
                    intent_name=intent_name,
                    message="Sounds like you don't know the zip code. Let me connect you to an agent",
                    session_attributes=session_attributes,
                )

            # Step 5. Confirm zip code
            if not slots.get('confirmZip') or not slots['confirmZip'].get('value'):
                return self.elicit_slot_response(
                    'confirmZip',
                    f'That zip code is {zip_code}. Right?',
                    session_attributes,
                    intent_object,
                )

            confirm_zip = None
            if (
                slots.get('confirmZip')
                and slots['confirmZip'].get('value')
                and slots['confirmZip']['value'].get('interpretedValue')
            ):
                confirm_zip = slots['confirmZip']['value']['interpretedValue'].lower()

            if confirm_zip is None:
                return self.elicit_slot_response(
                    'confirmZip',
                    f"Sorry, I didn't understand. Is {zip_code} the correct zip code? Please say yes or no.",
                    session_attributes,
                    intent_object,
                )
            elif 'no' in confirm_zip:
                intent_object['slots']['zipCode'] = None
                intent_object['slots']['confirmZip'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    "My mistake. Let's try again. Please say the five digit zip code where you'd like me to search like this 1 2 3 0 0. Or enter it on your keypad.",
                    session_attributes,
                    intent_object,
                )
            elif 'yes' in confirm_zip or 'right' in confirm_zip:
                intent_object['slots']['confirmZip'] = None
                # Step 6. Ask about card needs
                if not slots.get('needsCard') or not slots['needsCard'].get('value'):
                    return self.elicit_slot_response(
                        'needsCard',
                        'Thanks. Do you need to get a Social Security card?',
                        session_attributes,
                        intent_object,
                    )

                # Step 7. Check nextAction
                if not slots.get('nextAction') or not slots['nextAction'].get('value'):
                    return self.elicit_slot_response(
                        'nextAction',
                        "What would you like to do next? Say 'repeat that' to hear the info again, 'local office' for local office details, 'change zip code' to search another area, 'return to menu' to start over, or 'finished' to end.",
                        session_attributes,
                        intent_object,
                    )

                next_action = slots['nextAction']['value']['interpretedValue'].lower()

                if 'repeat' in next_action:
                    intent_object['slots']['nextAction'] = None
                    return self.delegate_response(session_attributes, intent_object)
                elif 'local office' in next_action:
                    session_attributes.update({'needsCard': 'no'})
                    intent_object['slots']['nextAction'] = None
                    return self.delegate_response(session_attributes, intent_object)
                elif 'change zip code' in next_action:
                    intent_object['slots']['zipCode'] = None
                    intent_object['slots']['confirmZip'] = None
                    intent_object['slots']['needsCard'] = None
                    intent_object['slots']['nextAction'] = None
                    return self.elicit_slot_response(
                        'zipCode',
                        "Alright, let's look somewhere else. Please say the five digit zip code.",
                        session_attributes,
                        intent_object,
                    )
                elif 'finished' in next_action:
                    return self.close_response(
                        intent_name=intent_name,
                        message='Goodbye.',
                        session_attributes=session_attributes,
                    )
                elif 'return to menu' in next_action:
                    session_attributes.update({'action': 'ReturnToMenu'})
                    return {
                        'sessionState': {
                            'dialogAction': {'type': 'ElicitIntent'},
                            'intent': None,
                            'sessionAttributes': session_attributes,
                        },
                        'messages': [
                            {
                                'contentType': 'PlainText',
                                'content': 'Returning to the main menu. How can I assist you now?',
                            }
                        ],
                    }
                else:
                    intent_object['slots']['nextAction'] = None
                    return self.elicit_slot_response(
                        'nextAction',
                        "Sorry, I didn't understand. Say 'repeat that', 'local office', 'change zip code', 'return to menu', or 'finished'.",
                        session_attributes,
                        intent_object,
                    )

        # Fallback for unexpected intents
        return self.close_response(
            intent_name=intent_name,
            message="Sorry, I didn’t understand. Please say 'office' to locate an office.",
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

            if not zip_code:
                return self.elicit_slot_response(
                    'zipCode',
                    'I need a zip code to provide office information. Please say or enter a five-digit zip code.',
                    session_attributes,
                    intent_object,
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

            # Mock API call to check if Card Center exists
            card_center_in_zip_result = random.choice(
                [True, True, True, True, True, False]
            )
            if not card_center_in_zip_result and 'yes' in needs_card:
                session_attributes.update({'zipCode': zip_code})
                intent_object['slots']['zipCode'] = None
                intent_object['slots']['confirmZip'] = None
                intent_object['slots']['needsCard'] = None
                intent_object['slots']['nextAction'] = None
                return self.elicit_slot_response(
                    'zipCode',
                    f'No Social Security card center was found in {zip_code}. Please provide a different five-digit zip code.',
                    session_attributes,
                    intent_object,
                )

            # SUCCESS - provide info based on user needs
            if 'yes' in needs_card:
                message = f"Alright. To apply for a new or replacement Social Security card, you'll need to visit the card center in your area which is located at 123 Main St, City, State, {zip_code}. The hours of operation are, Monday through Friday 9 AM to 4 PM. "
            else:
                message = f'Here is information for the local Social Security office in zip code {zip_code}. The address is 456 Office St, City, State. Hours are Monday through Friday 9 AM to 4 PM. Phone is 1-800-555-0199. '

            message += "To hear that again, say, repeat that. For information about the local Social Security office, say local office. To search a different zip code, say change zip code. Or if you're finished, just say, I'm finished."

            session_attributes.update(
                {'action': 'ReturnToMenu', 'zipCode': zip_code, 'needsCard': needs_card}
            )

            return self.close_response(
                intent_name=intent_name,
                message=message,
                session_attributes=session_attributes,
            )

        # Fallback for unexpected intents
        return self.close_response(
            intent_name=intent_name,
            message="Sorry, I didn’t understand. Please say 'office' to locate an office.",
            session_attributes=session_attributes,
        )

    def repeat_response(self, session_attributes, intent_object):
        """Repeat the last office info using stored zipCode and needsCard"""
        zip_code = session_attributes.get('zipCode')
        needs_card = session_attributes.get('needsCard', 'no').lower()
        if not zip_code:
            return self.elicit_slot_response(
                'zipCode',
                "I don't have a zip code to repeat. Please provide a five-digit zip code.",
                session_attributes,
                {
                    'name': 'LocateOffice',
                    'slots': {
                        'zipCode': None,
                        'needsCard': None,
                        'confirmZip': None,
                        'nextAction': None,
                    },
                },
            )
        if 'yes' in needs_card:
            message = f"Alright. To apply for a new or replacement Social Security card, you'll need to visit the card center in your area which is located at 123 Main St, City, State, {zip_code}. The hours of operation are, Monday through Friday 9 AM to 4 PM. "
        else:
            message = f'Here is information for the local Social Security office in zip code {zip_code}. The address is 456 Office St, City, State. Hours are Monday through Friday 9 AM to 4 PM. Phone is 1-800-555-0199. '
        message += "To hear that again, say, repeat that. For information about the local Social Security office, say local office. To search a different zip code, say change zip code. Or if you're finished, just say, I'm finished."
        return self.close_response(
            intent_name='LocateOffice',
            message=message,
            session_attributes=session_attributes,
        )

    def local_office_info_response(self, session_attributes, intent_object):
        """Provide local office info using stored zipCode"""
        zip_code = session_attributes.get('zipCode')
        if not zip_code:
            return self.elicit_slot_response(
                'zipCode',
                'Please provide a five-digit zip code for the local office information.',
                session_attributes,
                {
                    'name': 'LocateOffice',
                    'slots': {
                        'zipCode': None,
                        'needsCard': None,
                        'confirmZip': None,
                        'nextAction': None,
                    },
                },
            )
        message = f'Here is information for the local Social Security office in zip code {zip_code}. The address is 456 Office St, City, State. Hours are Monday through Friday 9 AM to 4 PM. Phone is 1-800-555-0199. '
        message += "To hear that again, say, repeat that. To search a different zip code, say change zip code. Or if you're finished, just say, I'm finished."
        return self.close_response(
            intent_name='LocateOffice',
            message=message,
            session_attributes=session_attributes,
        )

    def finished_response(self, session_attributes, intent_object):
        """End the session"""
        return self.close_response(
            intent_name='Finished',
            message='Goodbye.',
            session_attributes=session_attributes,
        )

    def return_to_menu_response(self, session_attributes, intent_object):
        """Return to main menu"""
        session_attributes.update({'action': 'ReturnToMenu'})
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'intent': None,
                'sessionAttributes': session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'Returning to the main menu. How can I assist you now?',
                }
            ],
        }

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
            }
        }

    def close_response(self, message, intent_name, session_attributes):
        """Build "conversation finished" response"""
        return {
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


# Create handler instance
handler_instance = OfficeLocatorHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)


# P1110: Initial zipcode collection
# 'Okay, office information. One moment. Go ahead and say or enter the five digit zip code for your area or the area where you want to find an office.'

# P1118: Zipcode confirmation (conditional)
# 'That zip code is {zipCode}. Right?'

# P1121: Card center question (conditional)
# 'Thanks. Do you need to get a Social Security card?'

# P1122: Next action (conditional)
# 'To hear that again, say repeat that. For information about the local Social Security office, say local office. To search in a different zip code, say change zip code. Or if you are finished, just say, I am finished.'

# P1123: New zip code collection
# 'Alright, let us look somewhere else. What is the zip code?'


# if last_message_type == 'card_center' and card_center_info:
#     message = (
#         f'Alright. To apply for a new or replacement Social Security card, you will need to visit the card center '
#         f'in your area which is located at {card_center_info["address"]}. The hours of operation are, '
#         f'{card_center_info["hours"]}. And the phone number is {card_center_info["phone"]}.'
#     )
# elif last_message_type == 'local_office' and office_info:
#     zip_code = session_attributes.get('last_zip_code')
#     message = (
#         f'Okay, here is information for the servicing office in the zip code {zip_code}. '
#         f'The street address is {office_info["address"]}. The hours of operation are, '
#         f'{office_info["hours"]}. And the phone number is {office_info["phone"]}.'
#     )
# else:
#     message = 'I am sorry, I do not have anything to repeat right now.'

# follow_up = (
#     'To hear that again, say repeat that. Otherwise, to search a different zip code, say change zip code. '
#     'Or if you are finished, just say, I am finished.'
# )
