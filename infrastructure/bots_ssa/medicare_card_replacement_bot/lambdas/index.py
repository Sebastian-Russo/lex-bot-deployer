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
        intent_object = event['sessionState']['intent']  # Full object
        intent_name = self.get_intent_name(event)  # String
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'ProcessMedicareCardReplacement':
            # 1. Check filled: privacy agreement
            if not slots.get('privacyAcknowledgment'):
                # 2. If not, elicit privacy acknowledgment
                return self.elicit_slot_response(
                    slot_name='privacyAcknowledgment',
                    # P1045 & P1173
                    message='Before I can access your records, I will need to ask a question or two to verify who you are. Social Security is allowed to collect this information under the Social Security Act and the collect meets the requirements of the Paperwork Reduction Act under OMB number 0 9 6 0 0 5 9 6. The whole process should take about four minutes. To hear detailed information about the Privacy Act or Paperwork Reduction Act, say more information. Otherwise, say continue.',
                    session_attributes=session_attributes,
                    intent=intent_object,
                )
            # 3. Get value: privacy agreement
            privacy_value = slots['privacyAcknowledgment']['value'][
                'interpretedValue'
            ].lower()
            # 4. Check value
            if privacy_value == 'more':
                # Handle additional route: more info request
                return  # TODO: [Privacy and Paperwork Reduction Act] block
            # 4. Check value
            if privacy_value == 'no':
                # TODO: End conversation (transfer to agent)
                return
            # 4. Check value: If privacy agreement is "continue", move to terms agreement
            if privacy_value == 'continue':
                # 1. Check filled: terms agreement
                if not slots.get('termsAgreement'):
                    # 2. If not, elicit terms agreement
                    return self.elicit_slot_response(
                        slot_name='termsAgreement',
                        # P1010
                        message='Please note that any person who makes a false representation in an effort to alter or obtain information from the Social Security Administration may be punished by a fine or imprisonment or both. Do you understand and agree to these terms?',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )
                # 3. Get value: terms agreement
                terms_value = slots['termsAgreement']['value'][
                    'interpretedValue'
                ].lower()
                # 4. Check value
                if terms_value == 'more':
                    # Handle additional route: more info request
                    return  # TODO: [Privacy and Paperwork Reduction Act] block
                # 4. Check value
                if terms_value == 'no':
                    # TODO:
                    # Response: P1022: (In-Hour): "Without your agreement, I will not be able to help you with anything that requires access to personal information. Hold on while I get someone to help you."
                    # Action:Transfer to queue (to agent)
                    # Response: P1022: (Out-Hour): "Without your agreement, I will not be able to help you with anything that requires access to personal information."
                    # Action: Transfer to ? (hang up)
                    return
                # 4. Check value, if yes, move to next slot (SSN)
                if terms_value == 'yes':
                    # 1. Check filled: SSN
                    if not slots.get('socialSecurityNumber'):
                        # 2. If not, elicit SSN
                        return self.elicit_slot_response(
                            slot_name='socialSecurityNumber',
                            message='Please provide your SSN',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    # 3. Get value: SSN
                    ssn_value = slots['socialSecurityNumber']['value'][
                        'interpretedValue'
                    ]
                    # 4. Check value: If SSN is valid, move to next slot (DOB)
                    if ssn_value:
                        # 1. Check filled: DOB
                        if not slots.get('dateOfBirth'):
                            # 2. If not, elicit DOB
                            return self.elicit_slot_response(
                                slot_name='dateOfBirth',
                                message='Please provide your date of birth',
                                session_attributes=session_attributes,
                                intent=intent_object,
                            )
                        # 3. Get value: DOB
                        dob_value = slots['dateOfBirth']['value']['interpretedValue']
                        # 4. Check value: If DOB is valid, move to next slot (First Name)
                        if dob_value:
                            # 1. Check filled: First Name
                            if not slots.get('firstName'):
                                # 2. If not, elicit First Name
                                return self.elicit_slot_response(
                                    slot_name='firstName',
                                    message='Please provide your first name',
                                    session_attributes=session_attributes,
                                    intent=intent_object,
                                )
                            # 3. Get value: First Name
                            first_name_value = slots['firstName']['value'][
                                'interpretedValue'
                            ]
                            # 4. Check value: If First Name is valid, move to next slot (Last Name)
                            if first_name_value:
                                # 1. Check filled: Last Name
                                if not slots.get('lastName'):
                                    # 2. If not, elicit Last Name
                                    return self.elicit_slot_response(
                                        slot_name='lastName',
                                        message='Please provide your last name',
                                        session_attributes=session_attributes,
                                        intent=intent_object,
                                    )
                                # 3. Get value: Last Name
                                last_name_value = slots['lastName']['value'][
                                    'interpretedValue'
                                ]
                                # 4. Check value: If Last Name is valid, move to next submit request
                                if last_name_value:
                                    # TODO: have all slots filled, move to fulfillment hook
                                    return self.delegate_response(
                                        session_attributes=session_attributes,
                                        intent_object=intent_object,
                                    )

    def fulfillment_hook(self, event):
        """Handle fulfillment hook (Do the actual work with collected data)"""
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

    def close_response(self, message, session_attributes):
        """Build "conversation finished" response"""
        return


# Main response types you need:
# elicit_slot_response() - ask for specific slot
# delegate_response() - let Lex continue
# close_response() - end conversation
# elicit_intent_response() - ask for new intent


# Create handler instance
handler_instance = MedicareCardReplacementHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
