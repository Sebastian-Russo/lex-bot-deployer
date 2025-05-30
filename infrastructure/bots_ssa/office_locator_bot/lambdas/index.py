import json
import logging
import os
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
        """Main handler function"""
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

    def dialog_hook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle dialog code hook - controls conditional slot collection"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)

        logger.debug(f'Dialog hook - Intent: {intent_name}, Slots: {slots}')

        if intent_name == 'LocateOffice':
            return self.handle_locate_office_dialog(event, slots)
        elif intent_name == 'ChangeZipCode':
            return self.handle_change_zip_dialog(event, slots)
        else:
            # For utility intents, just delegate
            return self.delegate_response(event)

    def handle_locate_office_dialog(self, event, slots):
        """Handle conditional slot collection for LocateOffice intent"""
        zip_code = self.get_slot_value(slots, 'zipCode')
        confirm_zip = self.get_slot_value(slots, 'confirmZip')
        needs_card = self.get_slot_value(slots, 'needsCard')
        next_action = self.get_slot_value(slots, 'nextAction')

        # Step 1: Validate zipCode
        if zip_code:
            if not self.is_valid_zip_code(zip_code):
                # Invalid zip - re-ask with different message
                return self.elicit_slot_response(
                    event,
                    'zipCode',
                    'That is an invalid zip code. Let us try again. Please say the five digit zip code where you would like me to search. Like this, 1 2 3 0 0. Or enter it on your keypad.',
                )

            # Valid zip - ask for confirmation if not already confirmed
            if not confirm_zip:
                return self.elicit_slot_response(
                    event, 'confirmZip', f'That zip code is {zip_code}. Right?'
                )

            # Step 2: Handle confirmation
            if confirm_zip and not self.is_yes_response(confirm_zip):
                # User said no to confirmation - clear zipCode and re-ask
                return self.clear_slot_and_elicit(
                    event,
                    'zipCode',
                    'Okay, office information. One moment. Go ahead and say or enter the five digit zip code for your area or the area where you want to find an office.',
                    slots_to_clear=['zipCode', 'confirmZip'],
                )

            # Step 3: Zip confirmed - check if we need to ask about card
            if confirm_zip and self.is_yes_response(confirm_zip):
                # Look up if card center is available (would be actual API call)
                has_card_center = self.check_card_center_availability(zip_code)

                if has_card_center and not needs_card:
                    # Card center available - ask if they need card
                    return self.elicit_slot_response(
                        event,
                        'needsCard',
                        'Thanks. Do you need to get a Social Security card?',
                    )

                # Either no card center OR card question answered - check next action
                if not next_action:
                    # Need to ask what they want to do next
                    # This will be handled in fulfillment after providing office info
                    return self.delegate_response(event)

        # Let Lex handle other cases
        return self.delegate_response(event)

    def handle_change_zip_dialog(self, event, slots):
        """Handle dialog for ChangeZipCode intent"""
        new_zip_code = self.get_slot_value(slots, 'newZipCode')

        if new_zip_code and not self.is_valid_zip_code(new_zip_code):
            return self.elicit_slot_response(
                event,
                'newZipCode',
                'That is an invalid zip code. Let us try again. Please say the five digit zip code where you would like me to search. Like this, 1 2 3 0 0. Or enter it on your keypad.',
            )

        return self.delegate_response(event)

    def fulfillment_hook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment - provide office information and handle next actions"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = event.get('sessionAttributes', {})

        logger.debug(f'Fulfillment hook - Intent: {intent_name}, Slots: {slots}')

        if intent_name == 'LocateOffice':
            return self.fulfill_locate_office(event, slots, session_attributes)
        elif intent_name == 'ChangeZipCode':
            return self.fulfill_change_zip(event, slots, session_attributes)
        elif intent_name == 'RepeatRequest':
            return self.handle_repeat_request(event, session_attributes)
        elif intent_name == 'LocalOfficeInfo':
            return self.handle_local_office_info(event, session_attributes)
        elif intent_name == 'Finished':
            return self.handle_finished(event)
        elif intent_name == 'ReturnToMenu':
            return self.handle_return_to_menu(event)
        else:
            return self.close_response(event, 'Fulfilled', 'Thank you for calling.')

    def fulfill_locate_office(self, event, slots, session_attributes):
        """Provide office information based on zip code and card needs"""
        zip_code = self.get_slot_value(slots, 'zipCode')
        needs_card = self.get_slot_value(slots, 'needsCard')

        # Look up office information (would be actual API call)
        office_info = self.lookup_office_info(zip_code)
        card_center_info = self.lookup_card_center_info(zip_code)

        # Store info in session for repeat requests
        session_attributes['last_zip_code'] = zip_code
        session_attributes['office_info'] = json.dumps(office_info)
        session_attributes['card_center_info'] = (
            json.dumps(card_center_info) if card_center_info else None
        )

        if needs_card and self.is_yes_response(needs_card) and card_center_info:
            # P1122: Provide card center information
            message = (
                f'Alright. To apply for a new or replacement Social Security card, you will need to visit the card center '
                f'in your area which is located at {card_center_info["address"]}. The hours of operation are, '
                f'{card_center_info["hours"]}. And the phone number is {card_center_info["phone"]}.'
            )
            session_attributes['last_message_type'] = 'card_center'
        else:
            # P1112: Provide local office information
            message = (
                f'Okay, here is information for the servicing office in the zip code {zip_code}. '
                f'The street address is {office_info["address"]}. The hours of operation are, '
                f'{office_info["hours"]}. And the phone number is {office_info["phone"]}.'
            )
            session_attributes['last_message_type'] = 'local_office'

        # Now ask what they want to do next
        follow_up = (
            'To hear that again, say repeat that. For information about the local Social Security office, say local office. '
            'To search in a different zip code, say change zip code. Or if you are finished, just say, I am finished.'
        )

        return self.elicit_intent_response(
            event, message + ' ' + follow_up, session_attributes
        )

    def fulfill_change_zip(self, event, slots, session_attributes):
        """Handle new zip code search"""
        new_zip_code = self.get_slot_value(slots, 'newZipCode')

        # Transfer to LocateOffice intent with new zip code
        return self.elicit_intent_with_specific_intent(
            event,
            'LocateOffice',
            f'That zip code is {new_zip_code}. Right?',
            session_attributes,
        )

    def handle_repeat_request(self, event, session_attributes):
        """Handle repeat request"""
        last_message_type = session_attributes.get('last_message_type')
        office_info = json.loads(session_attributes.get('office_info', '{}'))
        card_center_info = (
            json.loads(session_attributes.get('card_center_info', '{}'))
            if session_attributes.get('card_center_info')
            else None
        )

        if last_message_type == 'card_center' and card_center_info:
            message = (
                f'Alright. To apply for a new or replacement Social Security card, you will need to visit the card center '
                f'in your area which is located at {card_center_info["address"]}. The hours of operation are, '
                f'{card_center_info["hours"]}. And the phone number is {card_center_info["phone"]}.'
            )
        elif last_message_type == 'local_office' and office_info:
            zip_code = session_attributes.get('last_zip_code')
            message = (
                f'Okay, here is information for the servicing office in the zip code {zip_code}. '
                f'The street address is {office_info["address"]}. The hours of operation are, '
                f'{office_info["hours"]}. And the phone number is {office_info["phone"]}.'
            )
        else:
            message = 'I am sorry, I do not have anything to repeat right now.'

        follow_up = (
            'To hear that again, say repeat that. Otherwise, to search a different zip code, say change zip code. '
            'Or if you are finished, just say, I am finished.'
        )

        return self.elicit_intent_response(
            event, message + ' ' + follow_up, session_attributes
        )

    def handle_local_office_info(self, event, session_attributes):
        """Handle local office information request"""
        zip_code = session_attributes.get('last_zip_code')
        office_info = json.loads(session_attributes.get('office_info', '{}'))

        if office_info and zip_code:
            message = (
                f'Okay, here is information for the servicing office in the zip code {zip_code}. '
                f'The street address is {office_info["address"]}. The hours of operation are, '
                f'{office_info["hours"]}. And the phone number is {office_info["phone"]}.'
            )
        else:
            message = 'I do not have office information available right now.'

        follow_up = (
            'To hear that again, say repeat that. Otherwise, to search a different zip code, say change zip code. '
            'Or if you are finished, just say, I am finished.'
        )

        return self.elicit_intent_response(
            event, message + ' ' + follow_up, session_attributes
        )

    def handle_finished(self, event):
        """Handle when user is finished"""
        session_attributes = {'action': 'ReturnToMainMenu'}
        return self.close_response(
            event,
            'Fulfilled',
            'Thank you for using our office locator service.',
            session_attributes,
        )

    def handle_return_to_menu(self, event):
        """Handle return to main menu"""
        session_attributes = {'action': 'ReturnToMainMenu'}
        return self.close_response(
            event, 'Fulfilled', 'Returning you to the main menu.', session_attributes
        )

    # Validation and lookup helper methods
    def is_valid_zip_code(self, zip_code: str) -> bool:
        """Validate zip code format"""
        if not zip_code:
            return False

        # Remove any non-digits
        digits_only = re.sub(r'\D', '', str(zip_code))

        # Must be exactly 5 digits
        return len(digits_only) == 5 and digits_only.isdigit()

    def is_yes_response(self, response: str) -> bool:
        """Check if response indicates yes"""
        if not response:
            return False

        response = response.lower().strip()
        yes_words = [
            'yes',
            'yeah',
            'yep',
            'correct',
            'right',
            'true',
            'y',
            'sure',
            'okay',
            'ok',
        ]
        return response in yes_words

    def check_card_center_availability(self, zip_code: str) -> bool:
        """Check if card center is available in zip code"""
        # TODO: Implement actual API call
        # For now, simulate that some zip codes have card centers
        return int(zip_code) % 2 == 0  # Even zip codes have card centers

    def lookup_office_info(self, zip_code: str) -> Dict[str, str]:
        """Look up office information for zip code"""
        # TODO: Implement actual API call
        # For now, return mock data
        return {
            'address': f'123 Main Street, City {zip_code}',
            'hours': 'Monday through Friday, 9 AM to 4 PM',
            'phone': '1-800-772-1213',
        }

    def lookup_card_center_info(self, zip_code: str) -> Dict[str, str]:
        """Look up card center information for zip code"""
        if not self.check_card_center_availability(zip_code):
            return None

        # TODO: Implement actual API call
        # For now, return mock data
        return {
            'address': f'456 Card Center Drive, City {zip_code}',
            'hours': 'Monday through Friday, 9 AM to 3 PM',
            'phone': '1-800-772-1213',
        }

    def get_slot_value(self, slots, slot_name):
        """Get the interpreted value of a slot"""
        slot = slots.get(slot_name)
        if slot and slot.get('value'):
            return slot['value'].get('interpretedValue', '')
        return None

    # Helper methods for Lex responses
    def get_intent_name(self, event):
        return event.get('sessionState', {}).get('intent', {}).get('name', '')

    def get_slots(self, event):
        return event.get('sessionState', {}).get('intent', {}).get('slots', {})

    def delegate_response(self, event):
        return {
            'sessionState': {
                'dialogAction': {'type': 'Delegate'},
                'intent': event.get('sessionState', {}).get('intent', {}),
                'sessionAttributes': event.get('sessionAttributes', {}),
            }
        }

    def elicit_slot_response(self, event, slot_name, message):
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_name},
                'intent': event.get('sessionState', {}).get('intent', {}),
                'sessionAttributes': event.get('sessionAttributes', {}),
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def clear_slot_and_elicit(self, event, slot_name, message, slots_to_clear=None):
        """Clear specified slots and elicit a new one"""
        current_intent = event.get('sessionState', {}).get('intent', {})
        current_slots = current_intent.get('slots', {}).copy()

        # Clear specified slots
        if slots_to_clear:
            for slot_to_clear in slots_to_clear:
                current_slots[slot_to_clear] = None

        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_name},
                'intent': {**current_intent, 'slots': current_slots},
                'sessionAttributes': event.get('sessionAttributes', {}),
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def elicit_intent_response(self, event, message, session_attributes=None):
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def elicit_intent_with_specific_intent(
        self, event, intent_name, message, session_attributes=None
    ):
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
                'intent': {'name': intent_name, 'state': 'InProgress', 'slots': {}},
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def close_response(
        self, event, fulfillment_state, message, session_attributes=None
    ):
        # Get current intent but fix the state for Close action
        current_intent = event.get('sessionState', {}).get('intent', {}).copy()
        current_intent['state'] = (
            'Fulfilled' if fulfillment_state == 'Fulfilled' else 'Failed'
        )

        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'fulfillmentState': fulfillment_state,
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
                'intent': current_intent,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }


# Create handler instance
handler_instance = OfficeLocatorHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
