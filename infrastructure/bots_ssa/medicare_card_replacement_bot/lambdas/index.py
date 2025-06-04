import json
import logging
import os
import random
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class MedicareCardReplacementHandler:
    """
    Handles Medicare Card Replacement bot conversation flow
    """

    def handler(self, event: Dict[str, Any], context=None) -> Dict[str, Any]:
        """Route to dialog_hook() or fulfillment_hook()"""
        logger.debug('Event: %s', json.dumps(event, indent=2))

        invocation_source = event.get('invocationSource')
        if invocation_source == 'DialogCodeHook':
            return self.dialog_hook(event)
        elif invocation_source == 'FulfillmentCodeHook':
            return self.fulfillment_hook(event)
        else:
            raise ValueError(f'Unknown invocation source: {invocation_source}')

    def get_slot_value(self, slots, slot_name):
        """Safely extract slot value, handling None cases"""
        slot = slots.get(slot_name)
        if not slot or not isinstance(slot, dict):
            return ''

        value = slot.get('value', {})
        if not isinstance(value, dict):
            return ''

        return (
            value.get('interpretedValue', '') or value.get('originalValue', '')
        ).lower()

    def dialog_hook(self, event):
        """Handle dialog hook"""
        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'ProcessMedicareCardReplacement':
            # Step 1: Privacy acknowledgment
            if not session_attributes.get('privacyAcknowledged') == 'true':
                # This block executes if privacy has NOT YET been acknowledged in the session.
                if not slots.get('privacyAcknowledgment'):
                    # Elicit slot if it's not present in the current event (first time asking)
                    return self.elicit_slot_response(
                        slot_name='privacyAcknowledgment',
                        message='Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. The whole process should take about four minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Slot 'privacyAcknowledgment' is present, process its value
                privacy_value = self.get_slot_value(slots, 'privacyAcknowledgment')
                logger.debug('Privacy value from slot: %s', privacy_value)

                if 'more' in privacy_value:
                    return self.elicit_slot_response(
                        slot_name='privacyAcknowledgment',
                        message='Privacy and Paperwork Reduction Act. Say Continue if you agree.',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                if 'no' in privacy_value or 'disagree' in privacy_value:
                    session_attributes['action'] = 'TransferToAgent'
                    session_attributes['reason'] = 'PrivacyDeclined'  # Corrected reason
                    return self.close_response(
                        intent_name=intent_name,
                        message='Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.',
                        session_attributes=session_attributes,
                    )

                # Check if the provided value means acknowledgment
                is_privacy_acknowledged_this_turn = (
                    'continue' in privacy_value
                    or 'yes' in privacy_value
                    or 'agree' in privacy_value
                )
                logger.debug(
                    'Is privacy acknowledged this turn: %s',
                    is_privacy_acknowledged_this_turn,
                )

                if is_privacy_acknowledged_this_turn:
                    session_attributes['privacyAcknowledged'] = 'true'
                    logger.info('Privacy acknowledged and set in session.')
                else:
                    # User provided a value, but it wasn't a recognized acknowledgment
                    if privacy_value:  # Ensure there was some input to respond to
                        return self.elicit_slot_response(
                            slot_name='privacyAcknowledgment',
                            message='Please say continue to proceed, or say more information for details about the Privacy Act.',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    else:
                        # Slot was present but value was empty, or some other edge case. Delegate.
                        logger.warning(
                            'Privacy slot present but value unclear or not an acknowledgment. Delegating.'
                        )
                        return self.delegate_response(session_attributes, intent_object)

            # Safeguard: If privacy is still not marked in session, something is wrong. Delegate.
            if not session_attributes.get('privacyAcknowledged') == 'true':
                logger.error(
                    'Error: Privacy not acknowledged in session after privacy block. Delegating.'
                )
                return self.delegate_response(session_attributes, intent_object)

            # Step 2: Terms agreement
            if not session_attributes.get('termsAgreed') == 'true':
                # This block executes if terms have NOT YET been agreed in the session.
                if not slots.get('termsAgreement'):
                    # Elicit slot if it's not present in the current event (first time asking)
                    return self.elicit_slot_response(
                        slot_name='termsAgreement',
                        message='Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Slot 'termsAgreement' is present, process its value
                terms_value = self.get_slot_value(slots, 'termsAgreement')
                logger.debug('Terms value from slot: %s', terms_value)

                if 'no' in terms_value or 'disagree' in terms_value:
                    session_attributes['action'] = 'TransferToAgent'
                    session_attributes['reason'] = 'TermsDeclined'
                    return self.close_response(
                        intent_name=intent_name,
                        message='Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you.',
                        session_attributes=session_attributes,
                    )

                is_terms_agreed_this_turn = (
                    'yes' in terms_value or 'agree' in terms_value
                )
                logger.debug(
                    'Are terms agreed this turn: %s', is_terms_agreed_this_turn
                )

                if is_terms_agreed_this_turn:
                    session_attributes['termsAgreed'] = 'true'
                    logger.info('Terms agreed and set in session.')
                else:
                    if terms_value:  # User provided a value, but not 'yes' or 'agree'
                        return self.elicit_slot_response(
                            slot_name='termsAgreement',
                            message='Please say yes or agree to continue, or say no if you disagree.',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    else:
                        logger.warning(
                            'Terms slot present but value unclear or not an agreement. Delegating.'
                        )
                        return self.delegate_response(session_attributes, intent_object)

            # Safeguard: If terms are still not marked in session, something is wrong. Delegate.
            if not session_attributes.get('termsAgreed') == 'true':
                logger.error(
                    'Error: Terms not agreed in session after terms block. Delegating.'
                )
                return self.delegate_response(session_attributes, intent_object)

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
            return self.fulfillment_hook(event)

        if intent_name == 'ReturnToMenu':
            return self.close_response(
                intent_name=intent_name,
                message='Thank you for calling.',
                session_attributes=session_attributes,
            )

        if intent_name == 'Finished':
            return self.close_response(
                intent_name=intent_name,
                message='Thank you for calling.',
                session_attributes=session_attributes,
            )

        return self.delegate_response(session_attributes, intent_object)

    def fulfillment_hook(self, event):
        """Handle fulfillment hook (Do the actual work with collected data)"""
        logger.info('>>>>>>>> Fulfillment hook called')
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'ProcessMedicareCardReplacement':
            # Extract user data
            ssn = slots['socialSecurityNumber']['value']['interpretedValue']
            dob = slots['dateOfBirth']['value']['interpretedValue']
            first_name = slots['firstName']['value']['interpretedValue']
            last_name = slots['lastName']['value']['interpretedValue']

            auth_result = random.choice(
                [
                    'SUCCESS',
                    'SUCCESS',
                    'SUCCESS',
                    'SUCCESS',
                    'SUCCESS',
                    'BLOCKED',
                    'FAILED',
                ]
            )

            if auth_result == 'BLOCKED':
                session_attributes.update(
                    {
                        'action': 'TransferToAgent',
                        'reason': 'AccountBlocked',
                    }
                )
                return self.close_response(
                    intent_name=intent_name,
                    message="According to our records, you asked that this automated system and our website block access to your account, so you'll need to speak to someone. By the way, if you want to unblock your account, the agent can help you do that as well. Hold on while I get someone to help you.",
                    session_attributes=session_attributes,
                )

            elif auth_result == 'FAILED':
                session_attributes.update(
                    {
                        'action': 'TransferToAgent',
                        'reason': 'AuthenticationFailed',
                        'processingStage': 'authentication',
                        'userSSN': ssn[-4:],  # Last 4 digits
                    }
                )
                return self.close_response(
                    intent_name=intent_name,
                    message="Sorry, I'm having trouble processing this request. Hold on while I get someone to help you.",
                    session_attributes=session_attributes,
                )

            elif auth_result == 'SUCCESS':
                session_attributes.update(
                    {
                        'action': 'ReturnToMenu',
                    }
                )
                return self.close_response(
                    intent_name=intent_name,
                    message="Alright. We're all set. You should receive your replacement Medicare card in the mail within four weeks. If you're finished, feel free to hang up. Otherwise, just hang on and I'll take you back to the Main Menu.",
                    session_attributes=session_attributes,
                )
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
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "Thank you. I've got everything I need. Hold on while I submit this.",
                }
            ],
        }

    def close_response(self, message, intent_name, session_attributes):
        """Build "conversation finished" response"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled',
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
