import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class PamphletHandler:
    def __init__(self):
        pass

    def handler(self, event, context=None):
        """Route to dialog_hook() or fulfillment_hook()"""
        logger.debug('Event: %s', json.dumps(event, indent=2))

        invocation_source = event.get('invocationSource')
        if invocation_source == 'DialogCodeHook':
            return self.dialog_hook(event)
        elif invocation_source == 'FulfillmentCodeHook':
            return self.fulfillment_hook(event)
        else:
            raise ValueError(f'Unknown invocation source: {invocation_source}')

    def dialog_hook(self, event):
        """Handle dialog code hook - controls conditional slot collection"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)

        logger.debug(
            'Dialog hook - Intent: %s, Slots: %s',
            intent_name,
            slots,
        )

        if intent_name == 'ProcessPamphletRequest':
            return
        else:
            # For utility intents, just delegate
            return

    def fulfillment_hook(self, event):
        """Handle fulfillment - determine final action based on collected slots"""
        intent_name = self.get_intent_name(event)
        slots = self.get_slots(event)
        session_attributes = event.get('sessionAttributes', {})

        logger.debug(
            'Fulfillment hook - Intent: %s, Slots: %s, Session Attributes: %s',
            intent_name,
            slots,
            session_attributes,
        )

        if intent_name == 'ProcessPamphletRequest':
            return  # TODO
        elif intent_name == 'RepeatRequest':
            return  # TODO
        elif intent_name == 'ReturnToMenu':
            return  # TODO
        else:
            return  # TODO

    ### Helper functions to extract data from Lex events ###

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


handler_instance = PamphletHandler()


def handler(event, context=None):
    """Lambda handler function"""
    # return handler_instance.handler(event, context)
    return 'Hello World'
