import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


def handler(event, context=None):
    """Handles medicare enrollment conversation flow"""

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
        print('Dialog hook - Event: %s', json.dumps(event, indent=2))

        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        if intent_name == 'MedicareEnrollment':
            print('Dialog hook - Intent: MedicareEnrollment')

            # check flowPhase
            # check confirmation slot
            # update session attributes based on slot value
            # clear the confirmation slot
            # return elicitSlotResponse

            flow_phase = session_attributes.get('flowPhase', 'main_flow')

            # Main Flow
            if flow_phase == 'main_flow':
                confirmation = slots.get('Confirmation', None)
                confirmation_value = ''
                # Check confirmation slot
                if confirmation and 'value' in confirmation:
                    confirmation_value = (
                        confirmation['value'].get('interpretedValue', '').lower()
                    )
                # Update session attributes based on slot value
                message = ''
                # If yes
                if confirmation_value == 'yes':
                    session_attributes['flowPhase'] = 'block_a'
                    message = 'P1370English'

                # If no
                elif confirmation_value == 'no':
                    session_attributes['flowPhase'] = 'main_flow'
                    message = 'P1378English + P1379English'
                # Clear the confirmation slot
                slots['Confirmation'] = None
                # Return elicitSlotResponse
                return self.elicit_slot_response(
                    slot_name='Confirmation',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

        return

    def fulfillment_hook(self, event: Dict[str, Any]):
        """Handle fulfillment hook"""
        print('Fulfillment hook - Event: %s', json.dumps(event, indent=2))

        intent_object = event['sessionState']['intent']
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        return

    return
