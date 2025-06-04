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
            return self.handle_conditional_slot_collection(event, slots)
        else:
            # For utility intents, just delegate
            return self.delegate_response(event)

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

    def get_intent_name(self, event):
        return event.get('sessionState', {}).get('intent', {}).get('name', '')

    def get_slots(self, event):
        return event.get('sessionState', {}).get('intent', {}).get('slots', {})

    def get_session_attributes(self, event):
        return event.get('sessionAttributes', {})

    def delegate_response(self, event):
        return {
            'sessionAttributes': event.get('sessionAttributes', {}),
            'dialogAction': {
                'type': 'Delegate',
                'intentName': self.get_intent_name(event),
            },
        }

    def close_response(self, event, fulfillment_state, message):
        return {
            'sessionAttributes': event.get('sessionAttributes', {}),
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': fulfillment_state,
                'message': {
                    'contentType': 'PlainText',
                    'content': message,
                },
            },
        }


handler_instance = PamphletHandler()


def handler(event, context=None):
    """Lambda handler function"""
    # return handler_instance.handler(event, context)
    return 'Hello World'
