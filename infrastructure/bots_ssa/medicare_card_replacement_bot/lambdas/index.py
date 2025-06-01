import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))

# Mock SSA API clients (replace with actual implementation)
# ssa_auth_client = boto3.client('lambda')  # Replace with actual SSA API client
# ssa_medicare_client = boto3.client('lambda')  # Replace with actual Medicare API client


class MedicareCardReplacementHandler:
    """
    Handles Mecicare Card Replacement bot conversation flow
    """

    # def __init__(self):
    # self.api_client = ssa_medicare_client

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        """Route to dialog_hook() or fulfillment_hook()"""
        logger.debug('Event: %s', json.dumps(event, indent=2))
        # self.helper = LexHelper(event)

        invocation_source = event.get('invocationSource')
        if invocation_source == 'DialogCodeHook':
            return self.dialog_hook(event)
        elif invocation_source == 'FulfillmentCodeHook':
            return self.fulfillment_hook(event)
        else:
            raise ValueError(f'Unknown invocation source: {invocation_source}')

    def dialog_hook(self, event):
        """Handle dialog hook"""
        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'ProcessMedicareCardReplacement':
            # Step 1: Privacy acknowledgment
            if not slots.get('privacyAcknowledgment'):
                return self.elicit_slot_response(
                    slot_name='privacyAcknowledgment',
                    message='Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. The whole process should take about four minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.',
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

        privacy_value = slots['privacyAcknowledgment']['value'][
            'interpretedValue'
        ].lower()

        # Handle privacy responses
        if 'more' in privacy_value:
            return self.elicit_slot_response(
                slot_name='privacyAcknowledgment',
                message='Privacy and Paperwork Reduction Act. Say Continue if you agree.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        if 'no' in privacy_value or 'disagree' in privacy_value:
            session_attributes['action'] = 'TransferToAgent'
            session_attributes['reason'] = 'TermsDeclined'
            return self.close_response(
                intent_name=intent_name,
                message='Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.',
                session_attributes=session_attributes,
            )

        if (
            'continue' not in privacy_value
            and 'yes' not in privacy_value
            and 'agree' not in privacy_value
        ):
            return self.elicit_slot_response(
                slot_name='privacyAcknowledgment',
                message='Please say continue or more information.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Step 2: Terms agreement
        if not slots.get('termsAgreement'):
            return self.elicit_slot_response(
                slot_name='termsAgreement',
                message='Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        terms_value = slots['termsAgreement']['value']['interpretedValue'].lower()

        if 'no' in terms_value or 'disagree' in terms_value:
            session_attributes['action'] = 'TransferToAgent'
            session_attributes['reason'] = 'TermsDeclined'
            return self.close_response(
                intent_name=intent_name,
                message='Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.',
                session_attributes=session_attributes,
            )

        if 'yes' not in terms_value and 'agree' not in terms_value:
            return self.elicit_slot_response(
                slot_name='termsAgreement',
                message='Please say yes or no.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Step 3: Social Security Number
        if not slots.get('socialSecurityNumber'):
            return self.elicit_slot_response(
                slot_name='socialSecurityNumber',
                message='Please provide your Social Security number.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Step 4: Date of Birth
        if not slots.get('dateOfBirth'):
            return self.elicit_slot_response(
                slot_name='dateOfBirth',
                message='Please provide your date of birth.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Step 5: First Name
        if not slots.get('firstName'):
            return self.elicit_slot_response(
                slot_name='firstName',
                message='Please provide your first name.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Step 6: Last Name
        if not slots.get('lastName'):
            return self.elicit_slot_response(
                slot_name='lastName',
                message='Please provide your last name.',
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # All slots filled - delegate to fulfillment
        return self.delegate_response(session_attributes, intent_object)

    def fulfillment_hook(self, event):
        """Handle fulfillment hook (Do the actual work with collected data)"""
        logger.info('>>>>>>>> Fulfillment hook called')
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)

        if intent_name == 'ProcessMedicareCardReplacement':
            name_first = slots.get('firstName')
            name_last = slots.get('lastName')
            dob = slots.get('dob')
            ssn = slots.get('socialSecurityNumber')

            # TODO: Call authentication API with user info
            # Handle authentication results:
            # SUCCESS → Call Medicare replacement API
            # BLOCKED → Set session attributes for agent transfer
            # FAILED → Set session attributes for agent transfer

            # TODO: Handle Medicare API results:
            # SUCCESS → Return success message
            # FAILED → Set session attributes for agent transfer

            return
        return

    ### Helper functions to extract data from Lex event ###

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
handler_instance = MedicareCardReplacementHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
