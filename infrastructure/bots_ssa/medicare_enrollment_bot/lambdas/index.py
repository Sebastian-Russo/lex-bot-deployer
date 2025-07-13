import json
import logging
import os
from typing import Any, Dict

# pylint: disable=import-error
from message_map import MessageMap  # noqa: E402

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class MedicareEnrollmentHandler:
    """Handle medicare enrollment conversation flow"""

    def __init__(self):
        pass

    def handler(self, event: Dict[str, Any], context=None):
        """Route to dialog_hook() or fulfillment_hook()"""
        logger.debug('Event: %s', json.dumps(event, indent=2))

        invocation_source = event.get('invocationSource')
        if invocation_source == 'DialogCodeHook':
            return self.dialog_hook(event)
        elif invocation_source == 'FulfillmentCodeHook':
            return self.fulfillment_hook(event)
        else:
            raise ValueError(f'Unknown invocation source: {invocation_source}')

    def dialog_hook(self, event: Dict[str, Any]):
        """Handle dialog hook"""
        logger.debug('Dialog hook - Event: %s', json.dumps(event, indent=2))

        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent(event)['name']
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'MedicareEnrollment':
            logger.debug('Dialog hook - Intent: MedicareEnrollment')

            # check flowPhase
            # check session attributes (confirmations)
            # check confirmation slot
            # update session attributes based on slot value
            # clear the confirmation slot
            # return elicitSlotResponse

            flow_phase = session_attributes.get('flowPhase', 'main_flow')

            # Main Flow
            if flow_phase == 'main_flow':
                confirmation = slots.get('Confirmation', None)
                confirmation_value = ''
                # Check session attributes (confirmations)

                # Check confirmation slot

                confirmation = session_attributes.get('Confirmation', None)

                confirmation_value = ''

                # TODO: check session attribtues and create logic
                # check step session attribute
                # check confirmation slot
                # update session attributes based on slot value
                # clear the confirmation slot
                # return elicitSlotResponse

                # Confirmation session_attribute values:
                # 1
                session_attributes = {
                    'flowPhase': 'main_flow' or 'block_a',
                    'step': {'step_1': {'enrollmentStatus': 'true' or 'false'}},
                }
                # 2
                session_attributes = {
                    'flowPhase': 'main_flow' or 'end_flow',
                    'step': {'step_2': {'needReplacementCard': 'true' or 'false'}},
                }
                # 3
                session_attributes = {
                    'flowPhase': 'main_flow' or 'end_flow',
                    'step': {'step_3': {'wantMedicationCostHelp': 'true' or 'false'}},
                }
                # 4
                session_attributes = {
                    'flowPhase': 'main_flow' or 'block_b',
                    'step': {
                        'step_4': {
                            'alreadyEnrolledInMedicationCostHelp_PartD': 'true'
                            or 'false'
                        }
                    },
                }
                # 5
                session_attributes = {
                    'flowPhase': 'main_flow' or 'repeat_p1375_p1376',
                    'step': {
                        'step_5': {'wantMedicationCostHelp_repeat': 'true' or 'false'}
                    },
                }
                # 6
                session_attributes = {
                    'flowPhase': 'end_flow',  # (transfer to ? Medicare Perscript Drug Extra help? bot or agent?)
                    'step': {'step_6': {'wantToReceiveApplication': 'true' or 'false'}},
                }

                # Check confirmation slot
                if confirmation and 'value' in confirmation:
                    confirmation_value = (
                        confirmation['value'].get('interpretedValue', '').lower()
                    )
                # Update session attribute flowPhase, based on slot value (yes/no)
                message = ''
                # If yes, transfer to block_a
                if confirmation_value == 'yes':
                    session_attributes['flowPhase'] = 'block_a'
                    message = MessageMap.get_message('P1370English')

                # If no, transfer to main_flow
                elif confirmation_value == 'no':
                    session_attributes['flowPhase'] = 'main_flow'
                    message = MessageMap.get_message('P1378English + P1379English')
                # Clear the confirmation slot
                slots['Confirmation'] = None
                # Return elicitSlotResponse
                return self.elicit_slot_response(
                    slot_name='Confirmation',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            if flow_phase == 'block_a':
                confirmation = slots.get('Confirmation', None)
                confirmation_value = ''
                # Check confirmation slot
                if confirmation and 'value' in confirmation:
                    confirmation_value = (
                        confirmation['value'].get('interpretedValue', '').lower()
                    )
                # Update session attribute flowPhase, based on slot value (yes/no)
                message = ''
                # If yes, repeat P1378 + P1379
                if confirmation_value == 'yes':
                    message = MessageMap.get_message('P1378English + P1379English')
                    # Clear the confirmation slot
                    slots['Confirmation'] = None
                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # If no, transfer to main menu, end_flow
                elif confirmation_value == 'no':
                    session_attributes['flowPhase'] = 'end_flow'
                    message = MessageMap.get_message('P1382English')
                    # Clear the confirmation slot
                    slots['Confirmation'] = None
                    # Return elicitSlotResponse
                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

            # TODO: only difference is a different message (rethink this logic)
            if flow_phase == 'block_b':
                confirmation = slots.get('Confirmation', None)
                confirmation_value = ''
                # Check confirmation slot
                if confirmation and 'value' in confirmation:
                    confirmation_value = (
                        confirmation['value'].get('interpretedValue', '').lower()
                    )
                # Update session attribute flowPhase, based on slot value (yes/no)
                message = ''
                # If yes, repeat P1380 + P1381
                if confirmation_value == 'yes':
                    message = MessageMap.get_message('P1380English + P1381English')
                    # Clear the confirmation slot
                    slots['Confirmation'] = None
                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # If no, transfer to main menu, end_flow
                elif confirmation_value == 'no':
                    session_attributes['flowPhase'] = 'end_flow'
                    message = MessageMap.get_message('P1382English')
                    # Clear the confirmation slot
                    slots['Confirmation'] = None
                    # Return elicitSlotResponse
                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

            if flow_phase == 'end_flow':
                return

        return

    def fulfillment_hook(self, event: Dict[str, Any]):
        """Handle fulfillment hook"""
        logger.debug('Fulfillment hook - Event: %s', json.dumps(event, indent=2))

        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent(event)['name']
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        return

    ### Helper functions to extract data from Lex events ###

    def get_intent(self, event):
        """Extract intent from event"""
        return event.get('sessionState', {}).get('intent', {})

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


handler_instance = MedicareEnrollmentHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
