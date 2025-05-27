import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class Reprint1099Handler:
    """
    Handles the conversation flow for SSA 1099 reprint requests
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
        """Handle dialog code hook - manages slot collection and validation"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = event.get('sessionAttributes', {})

        logger.debug(f'Dialog hook - Intent: {intent_name}, Slots: {slots}')

        # Handle different intents during dialog
        if intent_name == 'Start1099Request':
            return self.handle_birth_date_dialog(event, slots, session_attributes)
        elif intent_name == 'CurrentYear1099':
            return self.handle_current_year_dialog(event, slots, session_attributes)
        elif intent_name == 'PrivacyChoice':
            return self.handle_privacy_choice_dialog(event, slots, session_attributes)
        elif intent_name == 'TermsAgreement':
            return self.handle_terms_dialog(event, slots, session_attributes)
        elif intent_name == 'CollectSSN':
            return self.handle_ssn_collection_dialog(event, slots, session_attributes)
        else:
            return self.delegate_response(event)

    def fulfillment_hook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fulfillment code hook - executes business logic after slot collection"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = event.get('sessionAttributes', {})

        logger.debug(f'Fulfillment hook - Intent: {intent_name}, Slots: {slots}')

        if intent_name == 'Start1099Request':
            return self.fulfill_birth_date_check(event, slots, session_attributes)
        elif intent_name == 'CurrentYear1099':
            return self.fulfill_current_year_check(event, slots, session_attributes)
        elif intent_name == 'PrivacyChoice':
            return self.fulfill_privacy_choice(event, slots, session_attributes)
        elif intent_name == 'TermsAgreement':
            return self.fulfill_terms_agreement(event, slots, session_attributes)
        elif intent_name == 'RepeatRequest':
            return self.handle_repeat_request(event, session_attributes)
        elif intent_name == 'ReturnToMenu':
            return self.handle_return_to_menu(event)
        else:
            return self.close_response(event, 'Fulfilled', 'Thank you for calling.')

    def handle_birth_date_dialog(self, event, slots, session_attributes):
        """Handle birth date range question dialog"""
        birth_date_slot = slots.get('birthDateInRange')

        if not birth_date_slot or not birth_date_slot.get('value'):
            return self.delegate_response(event)

        # Validate the yes/no response
        response = birth_date_slot['value']['interpretedValue'].lower()
        if response not in ['yes', 'no']:
            return self.elicit_slot_response(
                event,
                'birthDateInRange',
                'Please answer yes or no. Are you born between December 15 and January 31?',
            )

        return self.delegate_response(event)

    def fulfill_birth_date_check(self, event, slots, session_attributes):
        """Handle the birth date check fulfillment"""
        birth_date_response = (
            slots.get('birthDateInRange', {})
            .get('value', {})
            .get('interpretedValue', '')
            .lower()
        )

        if birth_date_response == 'yes':
            # P1023: They should receive 1099 in mail by end of January
            session_attributes['last_message'] = 'P1023'
            return self.elicit_intent_response(
                event,
                f'Social Security beneficiaries will receive their 1099 statement in the mail by the end of January showing benefits they received in {self.current_tax_year}. Would you like to hear that again?',
                session_attributes,
            )
        else:
            # Move to next question - current year 1099
            session_attributes['conversation_step'] = 'current_year_check'
            return self.elicit_intent_with_specific_intent(
                event,
                'CurrentYear1099',
                f'Are you calling to get a replacement 1099 for the {self.current_tax_year} tax year?',
                session_attributes,
            )

    def handle_current_year_dialog(self, event, slots, session_attributes):
        """Handle current year 1099 question dialog"""
        current_year_slot = slots.get('wantCurrentYear')

        if not current_year_slot or not current_year_slot.get('value'):
            return self.delegate_response(event)

        return self.delegate_response(event)

    def fulfill_current_year_check(self, event, slots, session_attributes):
        """Handle current year check fulfillment"""
        wants_current_year = (
            slots.get('wantCurrentYear', {})
            .get('value', {})
            .get('interpretedValue', '')
            .lower()
        )

        if wants_current_year == 'yes':
            # P1013: Need to speak to agent for previous year
            session_attributes['transfer_reason'] = 'previous_year_1099'
            session_attributes['action'] = 'QueueTransfer'
            session_attributes['destination'] = self.agent_queue_arn
            return self.close_response(
                event,
                'Fulfilled',
                'To get a 1099 for a previous year, you need to speak to an agent. Hold on while I get someone to help you.',
                session_attributes,
            )
        else:
            # Start privacy and verification process
            session_attributes['conversation_step'] = 'privacy_intro'
            privacy_intro = (
                "Alright. Before I can access your records, I'll need to ask a question or two to verify who you are. "
                'Social Security is allowed to collect this information under the Social Security Act, and the collection '
                'meets the requirements of the Paperwork Reduction Act under OMB numbers 09600596 and 09600583. '
                'The whole process should take about six minutes. '
            )

            return self.elicit_intent_with_specific_intent(
                event,
                'PrivacyChoice',
                privacy_intro
                + 'To hear detailed information about the Privacy Act or Paper Reduction Act, say more information. Otherwise, say continue.',
                session_attributes,
            )

    def handle_privacy_choice_dialog(self, event, slots, session_attributes):
        """Handle privacy choice dialog"""
        return self.delegate_response(event)

    def fulfill_privacy_choice(self, event, slots, session_attributes):
        """Handle privacy choice fulfillment"""
        choice = (
            slots.get('privacyChoice', {})
            .get('value', {})
            .get('interpretedValue', '')
            .lower()
        )

        if choice == 'more_info':
            # Provide privacy act information (placeholder for now)
            privacy_info = (
                'The Privacy Act protects your personal information. The Paperwork Reduction Act '
                'ensures we only collect necessary information efficiently. '
            )
            return self.elicit_intent_with_specific_intent(
                event,
                'PrivacyChoice',
                privacy_info + "Say continue when you're ready to proceed.",
                session_attributes,
            )
        else:
            # Continue to terms agreement
            session_attributes['conversation_step'] = 'terms_agreement'
            return self.elicit_intent_with_specific_intent(
                event,
                'TermsAgreement',
                'Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?',
                session_attributes,
            )

    def handle_terms_dialog(self, event, slots, session_attributes):
        """Handle terms agreement dialog"""
        return self.delegate_response(event)

    def fulfill_terms_agreement(self, event, slots, session_attributes):
        """Handle terms agreement fulfillment"""
        agrees = (
            slots.get('agreeToTerms', {})
            .get('value', {})
            .get('interpretedValue', '')
            .lower()
        )

        if agrees == 'no':
            # P1022: Cannot help without agreement
            session_attributes['transfer_reason'] = 'no_terms_agreement'
            session_attributes['action'] = 'QueueTransfer'
            session_attributes['destination'] = self.agent_queue_arn
            return self.close_response(
                event,
                'Fulfilled',
                'Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.',
                session_attributes,
            )
        else:
            # Start SSN collection
            session_attributes['conversation_step'] = 'collect_ssn'
            return self.elicit_intent_with_specific_intent(
                event,
                'CollectSSN',
                "Alright, thanks. Let's keep going. First, please say your Social Security number one digit at a time. What is the first digit?",
                session_attributes,
            )

    def handle_ssn_collection_dialog(self, event, slots, session_attributes):
        """Handle SSN collection dialog - stopping at 3 digits for now"""
        # For now, we'll just collect first 3 digits as requested
        return self.delegate_response(event)

    def handle_repeat_request(self, event, session_attributes):
        """Handle repeat request"""
        last_message = session_attributes.get('last_message', '')

        if last_message == 'P1023':
            return self.elicit_intent_response(
                event,
                f'Social Security beneficiaries will receive their 1099 statement in the mail by the end of January showing benefits they received in {self.current_tax_year}. Would you like to hear that again?',
                session_attributes,
            )
        else:
            return self.elicit_intent_response(
                event,
                "I'm sorry, I don't have anything to repeat right now. How can I help you?",
                session_attributes,
            )

    def handle_return_to_menu(self, event):
        """Handle return to main menu"""
        # Set session attributes to indicate return to main SSA menu
        session_attributes = {'action': 'ReturnToMainMenu'}
        return self.close_response(
            event, 'Fulfilled', 'Returning you to the main menu.', session_attributes
        )

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

    def elicit_intent_with_specific_intent(
        self, event, intent_name, message, session_attributes=None
    ):
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
                'intent': {'name': intent_name, 'state': 'ReadyForFulfillment'},
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }

    def close_response(
        self, event, fulfillment_state, message, session_attributes=None
    ):
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'fulfillmentState': fulfillment_state,
                'sessionAttributes': session_attributes
                or event.get('sessionAttributes', {}),
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
        }


# Create handler instance
handler_instance = Reprint1099Handler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
