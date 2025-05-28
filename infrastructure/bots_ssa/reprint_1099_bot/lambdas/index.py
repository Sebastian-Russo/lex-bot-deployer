import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class Reprint1099Handler:
    """
    Handles the conversation flow for SSA 1099 reprint requests using true single intent approach
    """

    def __init__(self):
        self.current_tax_year = os.environ.get('CURRENT_TAX_YEAR', '2024')
        self.agent_queue_arn = os.environ.get('AGENT_QUEUE_ARN')

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

        if intent_name == 'Process1099Request':
            return self.handle_conditional_slot_collection(event, slots)
        else:
            # For utility intents, just delegate
            return self.delegate_response(event)

    def handle_conditional_slot_collection(self, event, slots):
        """Control which slots are required based on previous responses"""
        foreign_address = self.get_slot_value(slots, 'foreignAddress')
        current_year = self.get_slot_value(slots, 'currentYear')
        prior_years = self.get_slot_value(slots, 'priorYears')
        privacy_choice = self.get_slot_value(slots, 'privacyChoice')
        terms_agreement = self.get_slot_value(slots, 'termsAgreement')

        # Step 1: Always validate foreign address first
        if foreign_address and not self.is_valid_yes_no(foreign_address):
            return self.elicit_slot_response(
                event,
                'foreignAddress',
                'Please answer yes or no. Do you have a foreign address?',
            )

        # Step 2: If foreign address = Yes, skip all other slots (will transfer to agent)
        if foreign_address and self.normalize_yes_no(foreign_address) == 'yes':
            logger.debug('Foreign address = yes, skipping other slots')
            return self.delegate_response(event)  # Go straight to fulfillment

        # Step 3: If foreign address = No, require current year next
        if foreign_address and self.normalize_yes_no(foreign_address) == 'no':
            # If currentYear is not filled yet, elicit it
            if not current_year:
                return self.elicit_slot_response(
                    event,
                    'currentYear',
                    f'Are you calling to get a replacement 1099 for the {self.current_tax_year} tax year?',
                )

            # Validate current year response if it exists
            if current_year and not self.is_valid_yes_no(current_year):
                return self.elicit_slot_response(
                    event,
                    'currentYear',
                    f'Please answer yes or no. Are you calling to get a replacement 1099 for the {self.current_tax_year} tax year?',
                )

            # Step 4: If current year = No, require prior years next
            if current_year and self.normalize_yes_no(current_year) == 'no':
                # If priorYears is not filled yet, elicit it
                if not prior_years:
                    return self.elicit_slot_response(
                        event,
                        'priorYears',
                        'Are you calling to get a replacement 1099 for any of the prior 5 years?',
                    )

                # Validate prior years response if it exists
                if prior_years and not self.is_valid_yes_no(prior_years):
                    return self.elicit_slot_response(
                        event,
                        'priorYears',
                        'Please answer yes or no. Are you calling to get a replacement 1099 for any of the prior 5 years?',
                    )

                # Step 5: If prior years = No, skip remaining slots (will return to menu)
                if prior_years and self.normalize_yes_no(prior_years) == 'no':
                    logger.debug(
                        'Current year = no AND prior years = no, skipping remaining slots'
                    )
                    return self.delegate_response(event)  # Go to fulfillment

            # Step 6: If either current year or prior years = Yes, continue to privacy
            wants_any_year = (
                current_year and self.normalize_yes_no(current_year) == 'yes'
            ) or (prior_years and self.normalize_yes_no(prior_years) == 'yes')

            if wants_any_year:
                # If privacyChoice is not filled yet, elicit it
                if not privacy_choice:
                    return self.elicit_slot_response(
                        event,
                        'privacyChoice',
                        (
                            'Alright. Before I can access your records, I will need to ask a question or two to verify who you are. '
                            'Social Security is allowed to collect this information under the Social Security Act, and the collection '
                            'meets the requirements of the Paperwork Reduction Act under OMB numbers 09600596 and 09600583. '
                            'The whole process should take about six minutes. To hear detailed information about the Privacy Act or '
                            'Paperwork Reduction Act, say more information. Otherwise, say continue.'
                        ),
                    )

                # Validate privacy choice
                if privacy_choice and not self.is_valid_privacy_choice(privacy_choice):
                    return self.elicit_slot_response(
                        event,
                        'privacyChoice',
                        'Please say "more information" to hear about the Privacy Act, or say "continue" to proceed.',
                    )

                # Step 7: Handle "more information" response
                if (
                    privacy_choice
                    and self.normalize_privacy_choice(privacy_choice) == 'more_info'
                ):
                    return self.elicit_slot_response(
                        event,
                        'privacyChoice',
                        (
                            'The Privacy Act of 1974 protects your personal information. '
                            'The Paperwork Reduction Act ensures we only collect necessary information efficiently. '
                            'Social Security uses this information to verify your identity and provide you with the '
                            'services you requested. Say continue when you are ready to proceed.'
                        ),
                    )

                # Step 8: If privacy choice = continue, validate terms agreement
                if (
                    privacy_choice
                    and self.normalize_privacy_choice(privacy_choice) == 'continue'
                ):
                    # If termsAgreement is not filled yet, elicit it
                    if not terms_agreement:
                        return self.elicit_slot_response(
                            event,
                            'termsAgreement',
                            (
                                'Please note that any person who makes a false representation in an effort to alter or obtain '
                                'information from the Social Security Administration may be punished by a fine or imprisonment or both. '
                                'Do you understand and agree to these terms?'
                            ),
                        )

                    # Validate terms agreement response if it exists
                    if terms_agreement and not self.is_valid_yes_no(terms_agreement):
                        return self.elicit_slot_response(
                            event,
                            'termsAgreement',
                            'Please answer yes or no. Do you understand and agree to these terms?',
                        )

                    # Step 9: If terms agreement = No, skip SSN collection (will transfer to agent)
                    if (
                        terms_agreement
                        and self.normalize_yes_no(terms_agreement) == 'no'
                    ):
                        logger.debug('Terms agreement = no, skipping SSN collection')
                        return self.delegate_response(event)  # Go to fulfillment

        # Let Lex handle the remaining validation (SSN digits use AMAZON.Number)
        return self.delegate_response(event)

    def fulfillment_hook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment - determine final action based on collected slots"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = event.get('sessionAttributes', {})

        logger.debug(f'Fulfillment hook - Intent: {intent_name}, Slots: {slots}')

        if intent_name == 'Process1099Request':
            return self.process_1099_fulfillment(event, slots, session_attributes)
        elif intent_name == 'RepeatRequest':
            return self.handle_repeat_request(event, session_attributes)
        elif intent_name == 'ReturnToMenu':
            return self.handle_return_to_menu(event)
        else:
            return self.close_response(event, 'Fulfilled', 'Thank you for calling.')

    def process_1099_fulfillment(self, event, slots, session_attributes):
        """Process the 1099 request based on all collected slot values"""
        foreign_address = self.get_slot_value(slots, 'foreignAddress')
        current_year = self.get_slot_value(slots, 'currentYear')
        prior_years = self.get_slot_value(slots, 'priorYears')
        terms_agreement = self.get_slot_value(slots, 'termsAgreement')
        ssn_digit1 = self.get_slot_value(slots, 'ssnDigit1')

        logger.debug(
            f'Processing fulfillment - foreign_address: {foreign_address}, current_year: {current_year}, prior_years: {prior_years}'
        )

        # Case 1: Foreign address = Yes → Transfer to agent
        if foreign_address and self.normalize_yes_no(foreign_address) == 'yes':
            session_attributes['transfer_reason'] = 'foreign_address'
            session_attributes['action'] = 'QueueTransfer'
            session_attributes['destination'] = self.agent_queue_arn

            is_business_hours = self.is_business_hours()
            if is_business_hours:
                message = (
                    'Our automated system cannot process a 1099 or 1042 for you. '
                    'You can either hang up and use your online My SSA account or '
                    'hold on and I will get someone to help you.'
                )
            else:
                message = (
                    'Our automated system cannot process a 1099 or 1042 for you. '
                    'You can either hang up and use your online My SSA account or '
                    'call back during office hours.'
                )

            return self.close_response(event, 'Fulfilled', message, session_attributes)

        # Case 2: Doesn't want current year AND doesn't want prior years → Return to menu
        if (
            current_year
            and self.normalize_yes_no(current_year) == 'no'
            and prior_years
            and self.normalize_yes_no(prior_years) == 'no'
        ):
            session_attributes['action'] = 'ReturnToMainMenu'
            return self.close_response(
                event,
                'Fulfilled',
                'Returning you to the main menu.',
                session_attributes,
            )

        # Case 3: Terms agreement = No → Transfer to agent
        if terms_agreement and self.normalize_yes_no(terms_agreement) == 'no':
            session_attributes['transfer_reason'] = 'no_terms_agreement'
            session_attributes['action'] = 'QueueTransfer'
            session_attributes['destination'] = self.agent_queue_arn
            return self.close_response(
                event,
                'Fulfilled',
                (
                    'Without your agreement, I will not be able to help you with anything that requires '
                    'access to personal information. Hold on while I get someone to help you.'
                ),
                session_attributes,
            )

        # Case 4: Successfully collected SSN digits → Continue processing
        if ssn_digit1:
            return self.close_response(
                event,
                'Fulfilled',
                'Thank you. I have collected your information. Processing your 1099 request now...',
            )

        # Case 5: User wants current year or prior years but hasn't completed flow yet
        # This should continue the privacy/terms/SSN collection process
        if (current_year and self.normalize_yes_no(current_year) == 'yes') or (
            prior_years and self.normalize_yes_no(prior_years) == 'yes'
        ):
            # If we get here, something went wrong with slot collection
            logger.debug('User wants 1099 but slot collection incomplete')
            return self.close_response(
                event, 'Fulfilled', 'Let me continue processing your 1099 request...'
            )

        # Default case
        return self.close_response(event, 'Fulfilled', 'Thank you for calling.')

    def handle_repeat_request(self, event, session_attributes):
        """Handle repeat request"""
        return self.elicit_intent_response(
            event,
            'I am sorry, I do not have anything to repeat right now. How can I help you?',
            session_attributes,
        )

    def handle_return_to_menu(self, event):
        """Handle return to main menu"""
        session_attributes = {'action': 'ReturnToMainMenu'}
        return self.close_response(
            event, 'Fulfilled', 'Returning you to the main menu.', session_attributes
        )

    # Validation helper methods
    def is_valid_yes_no(self, response: str) -> bool:
        """Check if response is a valid yes/no"""
        if not response:
            return False

        response = response.lower().strip()
        yes_words = [
            'yes',
            'yeah',
            'yep',
            'yea',
            'correct',
            'right',
            'true',
            'y',
            'si',
            'sure',
            'okay',
            'ok',
        ]
        no_words = [
            'no',
            'nope',
            'nah',
            'incorrect',
            'wrong',
            'false',
            'n',
            'never',
            'nada',
        ]

        return response in yes_words or response in no_words

    def normalize_yes_no(self, response: str) -> str:
        """Normalize yes/no response to 'yes' or 'no'"""
        if not response:
            return ''

        response = response.lower().strip()
        yes_words = [
            'yes',
            'yeah',
            'yep',
            'yea',
            'correct',
            'right',
            'true',
            'y',
            'si',
            'sure',
            'okay',
            'ok',
        ]

        return 'yes' if response in yes_words else 'no'

    def is_valid_privacy_choice(self, response: str) -> bool:
        """Check if response is a valid privacy choice"""
        if not response:
            return False

        response = response.lower().strip()
        more_info_words = [
            'more information',
            'more info',
            'tell me more',
            'information',
            'details',
            'more',
        ]
        continue_words = [
            'continue',
            'proceed',
            'go on',
            'next',
            'go ahead',
            'keep going',
        ]

        return any(word in response for word in more_info_words) or any(
            word in response for word in continue_words
        )

    def normalize_privacy_choice(self, response: str) -> str:
        """Normalize privacy choice to 'more_info' or 'continue'"""
        if not response:
            return ''

        response = response.lower().strip()
        more_info_words = [
            'more information',
            'more info',
            'tell me more',
            'information',
            'details',
            'more',
        ]

        return (
            'more_info'
            if any(word in response for word in more_info_words)
            else 'continue'
        )

    def is_business_hours(self):
        """Check if it's currently business hours"""
        # TODO: Implement actual business hours logic based on current time
        # For now, always return True to test business hours flow
        return True

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

    def elicit_intent_response(self, event, message, session_attributes=None):
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
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
handler_instance = Reprint1099Handler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
