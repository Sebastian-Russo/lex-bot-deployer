import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict

import boto3
from helper import LexHelper

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))

# Mock SSA API clients (replace with actual implementation)
ssa_auth_client = boto3.client('lambda')  # Replace with actual SSA API client
ssa_medicare_client = boto3.client('lambda')  # Replace with actual Medicare API client


class MedicareCardReplacementHandler:
    """
    Handles Medicare Card Replacement conversation flow
    """

    def __init__(self):
        self.helper = None

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        """
        Main handler function for Lex events
        """
        logger.debug('Event: %s', json.dumps(event, indent=2))
        self.helper = LexHelper(event)

        try:
            invocation_source = event.get('invocationSource')
            if invocation_source == 'DialogCodeHook':
                return self.dialog_hook()
            elif invocation_source == 'FulfillmentCodeHook':
                return self.fulfillment_hook()
            else:
                raise ValueError(f'Unknown invocation source {invocation_source}')
        except Exception as e:
            logger.error(f'Unhandled Error: {str(e)}')
            return self.helper.failed_response(
                "I apologize, but I'm having technical difficulties. Let me transfer you to someone who can help."
            )

    def dialog_hook(self) -> Dict[str, Any]:
        """
        Controls slot collection flow and validates inputs
        """
        helper = self.helper
        intent = helper.event['sessionState']['intent']
        intent_name = helper.intent_name
        slots = helper.slots

        # Handle privacy information intent
        if intent_name == 'PrivacyInformation':
            privacy_info = (
                'The Privacy Act of 1974 protects the privacy and accuracy of records maintained by Federal agencies. '
                'The Paperwork Reduction Act requires that Federal agencies minimize the burden of data collection on the public. '
                'Social Security Administration OMB number 0960-0596 covers this collection. '
                'Now, to continue with your Medicare card replacement, say continue.'
            )
            return helper.elicit_intent(privacy_info)

        # Handle return to menu intent
        if intent_name == 'ReturnToMenu':
            helper.session_attributes['action'] = 'ReturnToMenu'
            return helper.fulfilled_response('Taking you back to the main menu.')

        # Handle FallbackIntent in dialog hook
        if intent_name == 'FallbackIntent':
            return helper.elicit_intent(
                'I can help you get a replacement Medicare card. '
                "Say 'medicare card replacement' or 'I need a new medicare card' to get started."
            )

        # Main Medicare card replacement flow
        if intent_name == 'ProcessMedicareCardReplacement':
            return self._handle_medicare_flow(slots)

        # Default delegate
        return helper.delegate()

    def _handle_medicare_flow(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the main Medicare card replacement conversation flow
        """
        helper = self.helper

        # Step 1: Initial greeting and privacy choice
        if not slots.get('privacyChoice'):
            # Check if this is the very first interaction
            if not helper.session_attributes.get('greeting_played'):
                greeting = (
                    'Okay. Medicare Replacement Card. One moment. '
                    'Did you know you can request a Replacement Medicare Card by going online '
                    'and using your My S S A account? Go to w w w dot social security dot g o v and select Sign in. '
                    'Before I can access your records, I will need to ask a question or two to verify who you are. '
                    'Social Security is allowed to collect this information under the Social Security Act '
                    'and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. '
                    'The whole process should take about four minutes. '
                    'To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. '
                    'Otherwise, say continue.'
                )
                helper.session_attributes['greeting_played'] = 'true'
                return helper.elicit_slot('privacyChoice', greeting)
            else:
                return helper.elicit_slot('privacyChoice')

        # Handle privacy choice
        privacy_choice = slots['privacyChoice']['value']['interpretedValue'].lower()
        if 'more' in privacy_choice or 'information' in privacy_choice:
            # Clear the slot and redirect to privacy information intent
            helper.clear_slot('privacyChoice')
            return helper.elicit_intent('Let me provide you with that information.')

        if 'continue' not in privacy_choice:
            # Re-ask for valid choice
            return helper.elicit_slot(
                'privacyChoice',
                "Please say either 'continue' to proceed, or 'more information' to learn about the Privacy Act.",
            )

        # Step 2: Terms agreement
        if not slots.get('termsAgreement'):
            return helper.elicit_slot(
                'termsAgreement',
                'Please note that any person who makes a false representation in an effort '
                'to alter or obtain information from the Social Security Administration may be '
                'punished by a fine or imprisonment or both. Do you understand and agree to these terms?',
            )

        # Handle terms agreement response
        terms_response = slots['termsAgreement']['value']['interpretedValue'].lower()
        if 'no' in terms_response or 'disagree' in terms_response:
            helper.session_attributes['action'] = 'TransferToAgent'
            helper.session_attributes['reason'] = 'TermsDeclined'
            return helper.fulfilled_response(
                'Without your agreement, I will not be able to help you with anything '
                'that requires access to personal information. Hold on while I get someone to help you.'
            )

        if 'yes' not in terms_response and 'agree' not in terms_response:
            return helper.elicit_slot(
                'termsAgreement',
                "Please say 'yes' if you agree to these terms, or 'no' if you do not agree.",
            )

        # Step 3: Collect and validate SSN
        if not slots.get('socialSecurityNumber'):
            return helper.elicit_slot(
                'socialSecurityNumber', 'Please provide your Social Security number.'
            )

        if not self._validate_ssn(
            slots['socialSecurityNumber']['value']['interpretedValue']
        ):
            helper.clear_slot('socialSecurityNumber')
            return helper.elicit_slot(
                'socialSecurityNumber',
                "I didn't get a valid Social Security number. Please provide your 9-digit Social Security number.",
            )

        # Step 4: Collect and validate date of birth
        if not slots.get('dateOfBirth'):
            return helper.elicit_slot(
                'dateOfBirth', 'Please provide your date of birth.'
            )

        if not self._validate_date_of_birth(
            slots['dateOfBirth']['value']['interpretedValue']
        ):
            helper.clear_slot('dateOfBirth')
            return helper.elicit_slot(
                'dateOfBirth',
                'I need your date of birth in a format like January 1st, 1950, or 01/01/1950.',
            )

        # Step 5: Collect first name
        if not slots.get('firstName'):
            return helper.elicit_slot('firstName', 'Please provide your first name.')

        if not self._validate_name(slots['firstName']['value']['interpretedValue']):
            helper.clear_slot('firstName')
            return helper.elicit_slot('firstName', 'Please provide your first name.')

        # Step 6: Collect last name
        if not slots.get('lastName'):
            return helper.elicit_slot('lastName', 'Please provide your last name.')

        if not self._validate_name(slots['lastName']['value']['interpretedValue']):
            helper.clear_slot('lastName')
            return helper.elicit_slot('lastName', 'Please provide your last name.')

        # All information collected - delegate to fulfillment
        return helper.delegate()

    def fulfillment_hook(self) -> Dict[str, Any]:
        """
        Handle fulfillment - authentication and Medicare card request submission
        """
        helper = self.helper
        intent_name = helper.intent_name

        # Handle utility intents
        if intent_name == 'PrivacyInformation':
            return helper.elicit_intent(
                'Is there anything else I can help you with today?'
            )

        if intent_name == 'ReturnToMenu':
            helper.session_attributes['action'] = 'ReturnToMenu'
            return helper.fulfilled_response('Taking you back to the main menu.')

        # Handle FallbackIntent - guide user to main intent
        if intent_name == 'FallbackIntent':
            return helper.elicit_intent(
                'I can help you get a replacement Medicare card. '
                "To get started, say 'medicare card replacement' or 'I need a new medicare card'."
            )

        # Main Medicare processing
        if intent_name == 'ProcessMedicareCardReplacement':
            return self._process_medicare_request()

        return helper.fulfilled_response("I'm not sure how to help with that request.")

    def _process_medicare_request(self) -> Dict[str, Any]:
        """
        Process the Medicare card replacement request
        """
        helper = self.helper
        slots = helper.slots

        # Extract user information
        ssn = slots['socialSecurityNumber']['value']['interpretedValue']
        dob = slots['dateOfBirth']['value']['interpretedValue']
        first_name = slots['firstName']['value']['interpretedValue']
        last_name = slots['lastName']['value']['interpretedValue']

        logger.info('Processing Medicare card replacement request')

        try:
            # Step 1: Authenticate user
            auth_result = self._authenticate_user(ssn, dob, first_name, last_name)

            if auth_result == 'BLOCKED':
                helper.session_attributes['action'] = 'TransferToAgent'
                helper.session_attributes['reason'] = 'AccountBlocked'
                return helper.fulfilled_response(
                    'According to our records, you asked that this automated system and our website '
                    "block access to your account, so you'll need to speak to someone. "
                    'By the way, if you want to unblock your account, the agent can help you do that as well. '
                    'Hold on while I get someone to help you.'
                )

            elif auth_result == 'FAILED':
                helper.session_attributes['action'] = 'TransferToAgent'
                helper.session_attributes['reason'] = 'AuthenticationFailed'
                return helper.fulfilled_response(
                    "I'm having trouble verifying your information. "
                    'Hold on while I get someone to help you.'
                )

            elif auth_result != 'SUCCESS':
                raise Exception(f'Unexpected authentication result: {auth_result}')

            # Step 2: Submit Medicare card replacement request
            submission_result = self._submit_medicare_request(
                ssn, first_name, last_name
            )

            if submission_result == 'SUCCESS':
                helper.session_attributes['action'] = 'ReturnToMenu'
                return helper.fulfilled_response(
                    "Thank you. I've got everything I need. Hold on while I submit this... "
                    "Alright. We're all set. You should receive your replacement Medicare card "
                    "in the mail within four weeks. If you're finished, feel free to hang up. "
                    "Otherwise, just hang on and I'll take you back to the Main Menu."
                )

            else:
                raise Exception(f'Medicare submission failed: {submission_result}')

        except Exception as e:
            logger.error(f'Error processing Medicare request: {str(e)}')
            helper.session_attributes['action'] = 'TransferToAgent'
            helper.session_attributes['reason'] = 'ProcessingError'
            return helper.fulfilled_response(
                "Sorry, I'm having trouble processing this request. "
                'Hold on while I get someone to help you.'
            )

    def _validate_ssn(self, ssn: str) -> bool:
        """Validate Social Security Number format"""
        if not ssn:
            return False

        # Remove any non-digits
        ssn_digits = re.sub(r'\D', '', ssn)

        # Should be exactly 9 digits
        if len(ssn_digits) != 9:
            return False

        # Basic validation - no all zeros, no invalid area numbers, etc.
        if ssn_digits == '000000000' or ssn_digits.startswith('000'):
            return False

        return True

    def _validate_date_of_birth(self, dob: str) -> bool:
        """Validate date of birth"""
        if not dob:
            return False

        try:
            # Try to parse the date in various formats
            # Lex should provide this in ISO format, but let's be flexible
            from dateutil import parser

            parsed_date = parser.parse(dob)

            # Check if date is reasonable (not in the future, not too old)
            now = datetime.now()
            if parsed_date.year > now.year or parsed_date.year < (now.year - 120):
                return False

            return True
        except:
            return False

    def _validate_name(self, name: str) -> bool:
        """Validate name format"""
        if not name or len(name.strip()) < 1:
            return False

        # Basic validation - should contain only letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name.strip()):
            return False

        return True

    def _authenticate_user(
        self, ssn: str, dob: str, first_name: str, last_name: str
    ) -> str:
        """
        Authenticate user with SSA systems
        Returns: 'SUCCESS', 'FAILED', 'BLOCKED'
        """
        try:
            # This would be replaced with actual SSA authentication API call
            auth_payload = {
                'ssn': ssn,
                'dateOfBirth': dob,
                'firstName': first_name,
                'lastName': last_name,
            }

            # Mock authentication - replace with actual API call
            logger.info('Calling SSA authentication API')

            # For demo purposes, return SUCCESS
            # In real implementation:
            # response = ssa_auth_client.invoke(...)
            # return parse_auth_response(response)

            return 'SUCCESS'

        except Exception as e:
            logger.error(f'Authentication API error: {str(e)}')
            return 'FAILED'

    def _submit_medicare_request(
        self, ssn: str, first_name: str, last_name: str
    ) -> str:
        """
        Submit Medicare card replacement request
        Returns: 'SUCCESS', 'FAILED'
        """
        try:
            # This would be replaced with actual Medicare API call
            request_payload = {
                'ssn': ssn,
                'firstName': first_name,
                'lastName': last_name,
                'requestType': 'REPLACEMENT_CARD',
            }

            # Mock submission - replace with actual API call
            logger.info('Calling Medicare replacement API')

            # For demo purposes, return SUCCESS
            # In real implementation:
            # response = ssa_medicare_client.invoke(...)
            # return parse_submission_response(response)

            return 'SUCCESS'

        except Exception as e:
            logger.error(f'Medicare submission API error: {str(e)}')
            return 'FAILED'


# Create handler instance
handler_instance = MedicareCardReplacementHandler()


def handler(event, context=None):
    """
    Lambda handler function
    """
    return handler_instance.handler(event, context)
