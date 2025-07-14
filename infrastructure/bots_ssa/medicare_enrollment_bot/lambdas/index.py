import json
import logging
import os
import time
from typing import Any, Dict

# pylint: disable=import-error
from message_map import MessageMap  # noqa: E402

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class MedicareEnrollmentHandler:
    """Handle Medicare enrollment conversation flow using a unified state machine approach

    This handler implements a unified state machine for managing Medicare enrollment conversations.
    Key features include:

    - Single state tracking via 'current_step' session attribute
    - Consolidated conversation steps in one array
    - Explicit terminal steps with is_terminal flag
    - Support for combined prompts
    - Comprehensive metrics tracking
    - Helper methods for step transitions, prompt processing, and terminal steps

    The state machine drives the conversation through a series of steps, each with
    defined prompts, retry prompts, and outcome paths based on user responses.
    """

    def __init__(self):
        pass

    def handler(self, event: Dict[str, Any], context=None):
        """Route to dialog_hook() or fulfillment_hook()"""
        invocation_source = event['invocationSource']

        if invocation_source == 'DialogCodeHook':
            return self.dialog_hook(event)
        elif invocation_source == 'FulfillmentCodeHook':
            return self.fulfillment_hook(event)
        else:
            raise ValueError(f'Unknown invocation source: {invocation_source}')

    def dialog_hook(self, event: Dict[str, Any]):
        """Handle dialog hook

        This method implements a unified state machine pattern to manage the conversation flow
        for the Medicare Enrollment intent. It tracks the current step in session attributes,
        processes user responses, and returns appropriate Lex responses.
        """
        logger.debug('Dialog hook - Event: %s', json.dumps(event, indent=2))

        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent(event)['name']
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        logger.debug('Dialog hook - Intent: %s, Slots: %s', intent_name, slots)
        logger.debug('Dialog hook - Session attributes: %s', session_attributes)

        # Initialize session attributes
        session_attributes = self._initialize_session_attributes(session_attributes)

        # Handle FallbackIntent by redirecting to MedicareEnrollment
        if intent_name == 'FallbackIntent':
            return self.elicit_intent_response(
                session_attributes=session_attributes,
                message='I can help you with Medicare enrollment. Would you like information about enrolling in Medicare?',
            )

        if intent_name == 'MedicareEnrollment':
            logger.debug('Dialog hook - Intent: MedicareEnrollment')

            # Track conversation metrics
            if 'metrics' not in session_attributes:
                session_attributes['metrics'] = {
                    'steps_completed': 0,
                    'retries': 0,
                    'start_time': str(int(time.time())),
                }

            # Define all conversation steps in a unified state machine
            conversation_steps = [
                {
                    'id': 'step_1',
                    'attribute': 'alreadyEnrolledInMedicare',
                    'prompt': 'P1370English',
                    'retry_prompt': 'P1370aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_2'},
                        'no': {'next': 'step_medicare_info'},  # formerly block_a
                    },
                },
                {
                    'id': 'step_2',
                    'attribute': 'needReplacementCard',
                    'prompt': 'P1372English',
                    'retry_prompt': 'P1372aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_transfer_card_replacement'},
                        'no': {'next': 'step_3'},
                    },
                },
                {
                    'id': 'step_3',
                    'attribute': 'wantMedicationCostHelp',
                    'prompt': 'P1373English',
                    'retry_prompt': 'P1373aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_4'},
                        'no': {'next': 'step_end_flow'},
                    },
                },
                {
                    'id': 'step_4',
                    'attribute': 'alreadyEnrolledInMedicationCostHelp_PartD',
                    'prompt': 'P1374English',
                    'retry_prompt': 'P1374aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_5'},
                        'no': {'next': 'step_extra_help_info'},  # formerly block_b
                    },
                },
                {
                    'id': 'step_5',
                    'attribute': 'wantMedicationCostHelp_repeat',
                    'prompt': 'P1375English + P1376English',
                    'retry_prompt': 'P1376aEnglish',
                    'outcomes': {
                        'yes': {
                            'next': 'step_repeat_info'
                        },  # formerly repeat_p1375_p1376
                        'no': {'next': 'step_6'},
                    },
                },
                {
                    'id': 'step_6',
                    'attribute': 'wantToReceiveApplication',
                    'prompt': 'P1377English',
                    'retry_prompt': 'P1377aEnglish',
                    'outcomes': {
                        'yes': {'next': 'step_transfer_extra_help'},
                        'no': {'next': 'step_end_flow'},
                    },
                },
                # Former block_a - Medicare info for non-enrolled users
                {
                    'id': 'step_medicare_info',
                    'attribute': 'wantMoreMedicareInfo',
                    'prompt': 'P1371English + P1378English',  # Combined prompts
                    'retry_prompt': 'P1378English',
                    'outcomes': {
                        'yes': {'next': 'step_provide_medicare_info'},
                        'no': {'next': 'step_end_flow'},
                    },
                },
                {
                    'id': 'step_provide_medicare_info',
                    'attribute': 'providedMedicareInfo',
                    'prompt': 'P1379English',
                    'is_terminal': True,  # This step ends the conversation
                },
                # Former block_b - Extra Help program info
                {
                    'id': 'step_extra_help_info',
                    'attribute': 'wantExtraHelpApplication',
                    'prompt': 'P1379English + P1380English',  # Combined prompts
                    'retry_prompt': 'P1380English',
                    'outcomes': {
                        'yes': {'next': 'step_transfer_extra_help'},
                        'no': {'next': 'step_end_flow'},
                    },
                },
                # Former repeat_p1375_p1376 - Repeat medication cost help info
                {
                    'id': 'step_repeat_info',
                    'attribute': 'wantExtraHelpAfterRepeat',
                    'prompt': 'P1375English + P1376English + P1380English',  # Combined prompts
                    'retry_prompt': 'P1380English',
                    'outcomes': {
                        'yes': {'next': 'step_transfer_extra_help'},
                        'no': {'next': 'step_end_flow'},
                    },
                },
                # Terminal steps
                {
                    'id': 'step_transfer_card_replacement',
                    'attribute': 'transferredToCardReplacement',
                    'prompt': 'TRANSFER_CARD_REPLACEMENT',
                    'is_terminal': True,
                },
                {
                    'id': 'step_transfer_extra_help',
                    'attribute': 'transferredToExtraHelp',
                    'prompt': 'TRANSFER_EXTRA_HELP',
                    'is_terminal': True,
                },
                {
                    'id': 'step_end_flow',
                    'attribute': 'conversationEnded',
                    'prompt': 'P1382English',
                    'is_terminal': True,
                },
            ]

            # Initialize conversation if needed
            if 'step' not in session_attributes:
                session_attributes['step'] = '{}'
                session_attributes['retry_count'] = 0
                session_attributes['current_step'] = 'step_1'
                current_step = conversation_steps[0]  # Start with first step

                # Return initial prompt
                message = MessageMap.get_message(current_step['prompt'])
                return self.elicit_slot_response(
                    slot_name='Confirmation',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            # Get current step
            current_step_id = session_attributes.get('current_step', 'step_1')
            current_step = next(
                (s for s in conversation_steps if s['id'] == current_step_id),
                conversation_steps[0],
            )

            logger.debug('Current step: %s', current_step_id)

            # Process confirmation slot
            confirmation = slots.get('Confirmation', None)
            confirmation_value = None
            logger.debug('Confirmation slot value: %s', confirmation)

            # Handle terminal steps (steps that end the conversation)
            if current_step.get('is_terminal', False):
                return self._handle_terminal_step(
                    session_attributes, current_step, intent_name
                )

            # Process user's response for non-terminal steps
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
                    return self._handle_step_transition(
                        session_attributes=session_attributes,
                        current_step=current_step,
                        outcome_type='yes',
                        conversation_steps=conversation_steps,
                        intent_name=intent_name,
                        intent_object=intent_object,
                        slots=slots,
                    )

                # Process NO response
                elif confirmation_value in [
                    'no',
                    'nope',
                    'nah',
                    'negative',
                    'incorrect',
                ]:
                    return self._handle_step_transition(
                        session_attributes=session_attributes,
                        current_step=current_step,
                        outcome_type='no',
                        conversation_steps=conversation_steps,
                        intent_name=intent_name,
                        intent_object=intent_object,
                        slots=slots,
                    )

                # Handle invalid responses
                else:
                    # Increment retry count
                    retry_count = session_attributes.get('retry_count', 0) + 1
                    session_attributes['retry_count'] = retry_count

                    # Update metrics
                    if 'metrics' in session_attributes:
                        metrics = json.loads(session_attributes['metrics'])
                        metrics['total_retries'] = metrics.get('total_retries', 0) + 1
                        session_attributes['metrics'] = json.dumps(metrics)

                    logger.debug('Invalid response, retry count: %s', retry_count)

                    # Use appropriate message based on retry count
                    message = self._process_combined_prompt(
                        current_step['retry_prompt']
                    )

                    # Clear confirmation slot
                    slots['Confirmation'] = None

                    return self.elicit_slot_response(
                        slot_name='Confirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

            # No confirmation value, elicit slot
            else:
                message = self._process_combined_prompt(current_step['prompt'])

                response = self.elicit_slot_response(
                    slot_name='Confirmation',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

                # Log the response being returned
                logger.debug(
                    'Dialog hook - Response: %s', json.dumps(response, indent=2)
                )

                return response

        # Log conversation summary before returning
        if 'metrics' in session_attributes:
            metrics = json.loads(session_attributes['metrics'])
            elapsed_time = int(time.time()) - int(metrics['start_time'])
            logger.debug(
                'Conversation summary - Steps completed: %s, Retries: %s, Duration: %s seconds',
                metrics['steps_completed'],
                metrics.get('total_retries', 0),
                elapsed_time,
            )

        # Default return if no conditions are met
        return self.delegate_response(session_attributes, intent_object)

    def fulfillment_hook(self, event: Dict[str, Any]):
        """Handle fulfillment hook

        This method is called when the conversation is ready for fulfillment.
        It checks the session attributes and user responses to determine the appropriate
        closing message or action.
        """
        logger.debug('Fulfillment hook - Event: %s', json.dumps(event, indent=2))

        # Extract necessary information from the event
        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent(event)['name']
        # We reference slots in debug logs to avoid lint warnings
        slots = self.get_slots(event)
        logger.debug('Fulfillment hook - Slots: %s', slots)
        session_attributes = self.get_session_attributes(event)

        # Check if we're in a terminal step
        current_step_id = session_attributes.get('current_step', 'step_1')
        logger.debug('Fulfillment hook - Current step: %s', current_step_id)

        # Find the terminal step by ID
        conversation_steps = [
            # Define all conversation steps (same as in dialog_hook)
            # This is a simplified version for fulfillment_hook
            {
                'id': 'step_transfer_card_replacement',
                'attribute': 'transferredToCardReplacement',
                'prompt': 'TRANSFER_CARD_REPLACEMENT',
                'is_terminal': True,
            },
            {
                'id': 'step_transfer_extra_help',
                'attribute': 'transferredToExtraHelp',
                'prompt': 'TRANSFER_EXTRA_HELP',
                'is_terminal': True,
            },
            {
                'id': 'step_end_flow',
                'attribute': 'conversationEnded',
                'prompt': 'P1382English',
                'is_terminal': True,
            },
            {
                'id': 'step_provide_medicare_info',
                'attribute': 'providedMedicareInfo',
                'prompt': 'P1379English',
                'is_terminal': True,
            },
        ]

        # Find the current step
        current_step = next(
            (s for s in conversation_steps if s['id'] == current_step_id),
            None,
        )

        if current_step and current_step.get('is_terminal', False):
            return self._handle_terminal_step(
                session_attributes, current_step, intent_name
            )

        # Default: delegate to Lex
        return self.delegate_response(session_attributes, intent_object)

    def _get_current_step_id(self, session_attributes):
        """Determine the current step ID based on session attributes

        This helper method examines the session attributes to determine which step
        the conversation is currently on in the main flow.

        Args:
            session_attributes: The session attributes dictionary

        Returns:
            str: The current step ID (e.g., 'step_1', 'step_2', etc.)
        """
        # In our unified approach, we directly store the current step
        return session_attributes.get('current_step', 'step_1')

    def _handle_step_transition(
        self,
        session_attributes,
        current_step,
        outcome_type,
        conversation_steps,
        intent_name,
        intent_object,
        slots,
    ):
        """Handle transition to the next step in the conversation flow

        This helper method manages the transition between conversation steps,
        including updating session attributes, retrieving the next step,
        and generating the appropriate response.

        Args:
            session_attributes: The session attributes dictionary
            current_step: The current step dictionary
            outcome_type: The type of outcome ('yes' or 'no')
            conversation_steps: The list of all conversation steps
            intent_name: The name of the intent
            intent_object: The intent object
            slots: The slots dictionary

        Returns:
            dict: The response object for Lex
        """
        # Deserialize the step attribute to a dictionary
        step_data = json.loads(session_attributes.get('step', '{}'))

        # Store the attribute value
        if current_step['id'] not in step_data:
            step_data[current_step['id']] = {}

        # Set attribute value based on outcome type
        step_data[current_step['id']][current_step['attribute']] = outcome_type == 'yes'

        # Serialize back to a JSON string
        session_attributes['step'] = json.dumps(step_data)

        # Get next step
        next_step_id = current_step['outcomes'][outcome_type]['next']
        session_attributes['current_step'] = next_step_id

        # Reset retry count for new step
        session_attributes['retry_count'] = 0

        # Update metrics
        if 'metrics' in session_attributes:
            metrics = json.loads(session_attributes['metrics'])
            metrics['steps_completed'] += 1
            session_attributes['metrics'] = json.dumps(metrics)

        # Get next step
        next_step = next(
            (s for s in conversation_steps if s['id'] == next_step_id),
            None,
        )

        if next_step:
            logger.debug('Moving to next step: %s', next_step['id'])

            # If next step is terminal, handle it immediately
            if next_step.get('is_terminal', False):
                return self._handle_terminal_step(
                    session_attributes, next_step, intent_name
                )

            # Otherwise, elicit slot for the next step
            message = self._process_combined_prompt(next_step['prompt'])

            # Clear confirmation slot
            slots['Confirmation'] = None

            return self.elicit_slot_response(
                slot_name='Confirmation',
                message=message,
                session_attributes=session_attributes,
                intent=intent_object,
            )

        # Default return if next step not found
        return self.delegate_response(session_attributes, intent_object)

    def _process_combined_prompt(self, prompt_key):
        """Process potentially combined prompts

        This helper method handles combined prompts (e.g., "P1375English + P1376English")
        by splitting them and joining the retrieved messages.

        Args:
            prompt_key: The prompt key or combined prompt keys

        Returns:
            str: The processed message
        """
        if '+' in prompt_key:
            prompt_parts = [p.strip() for p in prompt_key.split('+')]
            return ' '.join([MessageMap.get_message(p) for p in prompt_parts])

        return MessageMap.get_message(prompt_key)

    def _handle_terminal_step(self, session_attributes, step, intent_name):
        """Handle terminal steps that end the conversation

        This helper method processes terminal steps, updates session attributes,
        and returns the appropriate close response.

        Args:
            session_attributes: The session attributes dictionary
            step: The terminal step dictionary
            intent_name: The name of the intent

        Returns:
            dict: The close response object for Lex
        """
        logger.debug('Handling terminal step: %s', step['id'])

        # Deserialize the step attribute to a dictionary
        step_data = json.loads(session_attributes.get('step', '{}'))

        # Store the attribute value
        if step['id'] not in step_data:
            step_data[step['id']] = {}

        step_data[step['id']][step['attribute']] = True

        # Serialize back to a JSON string
        session_attributes['step'] = json.dumps(step_data)

        # For terminal steps, provide the message and close the conversation
        message = self._process_combined_prompt(step['prompt'])

        return self.close_response(
            session_attributes=session_attributes,
            intent_name=intent_name,
            message=message,
        )

    def _initialize_session_attributes(self, session_attributes):
        """Initialize session attributes if not present"""
        # Initialize step tracking if not present
        if 'step' not in session_attributes:
            session_attributes['step'] = '{}'

        # Initialize current step if not present
        if 'current_step' not in session_attributes:
            session_attributes['current_step'] = 'step_1'

        # Initialize retry count if not present
        if 'retry_count' not in session_attributes:
            session_attributes['retry_count'] = 0

        # Initialize metrics if not present
        if 'metrics' not in session_attributes:
            metrics = {
                'start_time': str(int(time.time())),
                'steps_completed': 0,
                'total_retries': 0,
            }
            session_attributes['metrics'] = json.dumps(metrics)

        return session_attributes

    def get_intent(self, event):
        """Extract intent from event"""
        return event['sessionState']['intent']

    def get_slots(self, event):
        """Extract slots from event"""
        return event['sessionState']['intent']['slots']

    def get_session_attributes(self, event):
        """Extract session attributes from event"""
        return event['sessionState'].get('sessionAttributes', {})

    def elicit_slot_response(self, slot_name, message, session_attributes, intent):
        """Return elicit slot response"""
        # Create a completely new object with just the name field
        simplified_intent = {'name': intent['name']}
        
        # Convert any dictionary values in session_attributes to strings
        string_session_attributes = {}
        for key, value in session_attributes.items():
            if isinstance(value, dict):
                string_session_attributes[key] = json.dumps(value)
            else:
                string_session_attributes[key] = value
        
        # Create a new response object with the simplified intent
        return {
            'sessionState': {
                'dialogAction': {'slotToElicit': slot_name, 'type': 'ElicitSlot'},
                'intent': simplified_intent,
                'sessionAttributes': string_session_attributes
            },
            'messages': [{'contentType': 'PlainText', 'content': message}]
        }

    def elicit_intent_response(self, session_attributes, message):
        """Return elicit intent response"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'sessionAttributes': session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': message}],
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
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled',
                },
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


handler_instance = MedicareEnrollmentHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
