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

            # session_attributes = {
            #     'flowPhase': 'main_flow' or 'block_a' or 'block_b' or 'end_flow',
            #     'step': {
            #         'step_1': {'enrollmentStatus': True or False},
            #         'step_2': {'needReplacementCard': True or False},
            #         # ... other steps with their attributes
            #     },
            #     'retry_count': 0  # Incremented for invalid responses
            # }

            # Define the main flow steps
            main_flow_steps = [
                {
                    'id': 'step_1',
                    'attribute': 'enrollmentStatus',
                    'prompt': 'P1370English',
                    'retry_prompt': 'P1370aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_2', 'phase': 'main_flow'},
                        'no': {'next': 'block_a', 'phase': 'block_a'},
                    },
                },
                {
                    'id': 'step_2',
                    'attribute': 'needReplacementCard',
                    'prompt': 'P1372English',
                    'retry_prompt': 'P1372aEnglish',
                    'outcomes': {
                        'yes': {
                            'next': 'transfer',  # Special case for transfer
                            'phase': 'end_flow',
                        },
                        'no': {'next': 'step_3', 'phase': 'main_flow'},
                    },
                },
                {
                    'id': 'step_3',
                    'attribute': 'wantMedicationCostHelp',
                    'prompt': 'P1373English',
                    'retry_prompt': 'P1373aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_4', 'phase': 'main_flow'},
                        'no': {'next': 'end_flow', 'phase': 'end_flow'},
                    },
                },
                {
                    'id': 'step_4',
                    'attribute': 'alreadyEnrolledInMedicationCostHelp_PartD',
                    'prompt': 'P1374English',
                    'retry_prompt': 'P1374aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_5', 'phase': 'main_flow'},
                        'no': {'next': 'block_b', 'phase': 'block_b'},
                    },
                },
                {
                    'id': 'step_5',
                    'attribute': 'wantMedicationCostHelp_repeat',
                    'prompt': 'P1375English + P1376English',
                    'retry_prompt': 'P1376aEnglish',
                    'outcomes': {
                        'yes': {
                            'next': 'repeat_p1375_p1376',
                            'phase': 'repeat_p1375_p1376',
                        },
                        'no': {'next': 'step_6', 'phase': 'main_flow'},
                    },
                },
                {
                    'id': 'step_6',
                    'attribute': 'wantToReceiveApplication',
                    'prompt': 'P1377English',
                    'retry_prompt': 'P1377aEnglish',
                    'outcomes': {
                        'yes': {'next': 'transfer_extra_help', 'phase': 'end_flow'},
                        'no': {'next': 'end_flow', 'phase': 'end_flow'},
                    },
                },
            ]

            # Get current flow phase
            flow_phase = session_attributes.get('flowPhase', 'main_flow')

            # Handle main flow
            if flow_phase == 'main_flow':
                # Initialize session if needed
                if 'step' not in session_attributes:
                    session_attributes['step'] = {}
                    session_attributes['retry_count'] = 0
                    current_step = main_flow_steps[0]  # Start with first step

                    # Return initial prompt
                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=MessageMap.get_message(current_step['prompt']),
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Determine current step in main flow
                current_step_id = self._get_current_step_id(session_attributes)
                # Get current step from main_flow_steps list
                current_step = next(
                    (s for s in main_flow_steps if s['id'] == current_step_id),
                    main_flow_steps[0],
                )

                # Process confirmation slot
                confirmation = slots.get('Confirmation', None)
                confirmation_value = None

                if confirmation and 'value' in confirmation:
                    confirmation_value = (
                        confirmation['value'].get('interpretedValue', '').lower()
                    )
                    logger.debug('Confirmation Value: %s', confirmation_value)

                    # Process YES response
                    if confirmation_value in [
                        'yes',
                        'yeah',
                        'correct',
                        'right',
                        'sure',
                        'ok',
                        'okay',
                    ]:
                        # Store the attribute value
                        if current_step['id'] not in session_attributes['step']:
                            session_attributes['step'][current_step['id']] = {}

                        session_attributes['step'][current_step['id']][
                            current_step['attribute']
                        ] = True

                        # Get outcome for yes response
                        outcome = current_step['outcomes']['yes']
                        next_step_id = outcome['next']
                        session_attributes['flowPhase'] = outcome['phase']

                        # Handle special cases
                        if next_step_id == 'transfer':
                            # Handle transfer to Medicare Card Replacement
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message(
                                    'TRANSFER_MEDICARE_CARD'
                                ),
                            )

                        if next_step_id == 'transfer_extra_help':
                            # Handle transfer to Medicare Prescription Drug Extra Help
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message('TRANSFER_EXTRA_HELP'),
                            )

                        if next_step_id == 'end_flow':
                            # End of conversation
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message('P1382English'),
                            )

                        # For now, we'll only handle main_flow steps
                        # Other phases will be implemented later
                        if outcome['phase'] != 'main_flow':
                            # For now, just end the conversation
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message('P1382English'),
                            )

                        # Find next step in main flow
                        next_step = next(
                            (s for s in main_flow_steps if s['id'] == next_step_id),
                            None,
                        )

                        if next_step:
                            # Reset retry count for new step
                            session_attributes['retry_count'] = 0

                            # Clear confirmation slot
                            slots['Confirmation'] = None

                            # Return prompt for next step
                            return self.elicit_slot_response(
                                slot_name='Confirmation',
                                message=MessageMap.get_message(next_step['prompt']),
                                session_attributes=session_attributes,
                                intent=intent_object,
                            )

                    # Process NO response
                    elif confirmation_value in [
                        'no',
                        'nope',
                        'nah',
                        'negative',
                        'incorrect',
                    ]:
                        # Store the attribute value
                        if current_step['id'] not in session_attributes['step']:
                            session_attributes['step'][current_step['id']] = {}

                        session_attributes['step'][current_step['id']][
                            current_step['attribute']
                        ] = False

                        # Get outcome for no response
                        outcome = current_step['outcomes']['no']
                        next_step_id = outcome['next']
                        session_attributes['flowPhase'] = outcome['phase']

                        # Handle special case for end of flow
                        if next_step_id == 'end_flow':
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message('P1382English'),
                            )

                        # For now, we'll only handle main_flow steps
                        # Other phases will be implemented later
                        if outcome['phase'] != 'main_flow':
                            # For now, just end the conversation
                            return self.close_response(
                                session_attributes=session_attributes,
                                intent_name=intent_name,
                                message=MessageMap.get_message('P1382English'),
                            )

                        # Find next step
                        next_step = next(
                            (s for s in main_flow_steps if s['id'] == next_step_id),
                            None,
                        )

                        if next_step:
                            # Reset retry count for new step
                            session_attributes['retry_count'] = 0

                            # Clear confirmation slot
                            slots['Confirmation'] = None

                            # Return prompt for next step
                            return self.elicit_slot_response(
                                slot_name='Confirmation',
                                message=MessageMap.get_message(next_step['prompt']),
                                session_attributes=session_attributes,
                                intent=intent_object,
                            )

                    # Handle Retry
                    else:
                        # Invalid response, retry
                        retry_count = session_attributes.get('retry_count', 0) + 1
                        session_attributes['retry_count'] = retry_count

                        # Use retry prompt if available and retry count is appropriate
                        message_id = (
                            current_step['retry_prompt']
                            if retry_count <= 2
                            else current_step['prompt']
                        )

                        # Clear confirmation slot
                        slots['Confirmation'] = None

                        return self.elicit_slot_response(
                            slot_name='Confirmation',
                            message=MessageMap.get_message(message_id),
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # No confirmation value, elicit slot
                else:
                    message_id = current_step['prompt']

                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=MessageMap.get_message(message_id),
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

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

    # Helper functions state machine

    def _get_current_step_id(self, session_attributes):
        ### Helper functions ###

        """Determine the current step ID based on session attributes

        This helper method examines the session attributes to determine which step
        the conversation is currently on in the main flow.

        Args:
            session_attributes: The session attributes dictionary

        Returns:
            str: The current step ID (e.g., 'step_1', 'step_2', etc.)
        """
        # If no steps have been processed yet, start with step_1
        if 'step' not in session_attributes or not session_attributes['step']:
            return 'step_1'

        # Check each step in order
        steps = ['step_1', 'step_2', 'step_3', 'step_4', 'step_5', 'step_6']

        # Iterate through steps to find the current step
        for i, step_id in enumerate(steps):
            # If this step isn't in session attributes yet, this is the current step
            if step_id not in session_attributes['step']:
                return step_id

            # If this is the last step, return it
            if i == len(steps) - 1:
                return step_id

            # If the next step isn't in session attributes, this is the current step
            next_step = steps[i + 1]
            if next_step not in session_attributes['step']:
                return next_step

        # Default to step_1 if we can't determine the current step
        return 'step_1'

    # Helper functions Lex events

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
        """Return elicit slot response"""
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': slot_name,
                },
                'intent': intent,
                'sessionAttributes': session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                },
            ],
        }

    def close_response(self, session_attributes, intent_name, message):
        """Return close response for fulfillment or transfer

        Args:
            session_attributes: The session attributes dictionary
            intent_name: The name of the intent
            message: The message to display to the user

        Returns:
            dict: The response object for Lex
        """
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close',
                },
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled',
                },
                'sessionAttributes': session_attributes,
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': message,
                },
            ],
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


handler_instance = MedicareEnrollmentHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
