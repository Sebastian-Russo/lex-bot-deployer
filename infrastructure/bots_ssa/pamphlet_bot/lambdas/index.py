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

    slot_names = {
        '1': 'UnderstandingSocialSecurity',
        '2': 'RetirementBenefits',
        '3': 'DisabilityBenefits',
        '4': 'SurvivorBenefits',
        '5': 'HowWorkAffectsBenefits',
        '6': 'BenefitsForChildrenWithDisabilities',
        '7': 'WhatEveryWomanShouldKnowAboutSocialSecurity',
    }

    def dialog_hook(self, event):
        """Handle dialog code hook - controls conditional slot collection"""
        intent_object = self.get_intent(event)
        intent_name = intent_object.get('name', '')
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)
        # selection, address, confirmation
        flow_phase = session_attributes.get('flowPhase', 'selection')
        logger.debug(
            'Dialog hook - Intent and Slots: %s, Flow Phase: %s, Session Attributes: %s',
            json.dumps(intent_object),
            json.dumps(flow_phase),
            json.dumps(session_attributes),
        )

        if intent_name == 'ProcessPamphletRequest':
            # flowPhone selection, no session attributes, initialize
            if (
                flow_phase == 'selection'
                and session_attributes.get('currentPamphletIndex', None) is None
            ):
                # If no session attributes, start at the beginning, initialize session attributes
                # Offer first pamphlet
                if 'currentPamphletIndex' not in session_attributes:
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',  # add 1 for first pamphlet
                            'flowPhase': 'selection',
                            'selectedPamphlets': json.dumps([]),
                        }
                    )
                return self.elicit_slot_response(
                    slot_name='UnderstandingSocialSecurity',
                    message='Would you like to hear the pamphlet on Understanding Social Security?',
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            # flowPhone selection, session attributes, continue
            if (
                flow_phase == 'selection'
                and session_attributes.get('currentPamphletIndex', None) is not None
            ):
                current_pamphlet_index = session_attributes.get(
                    'currentPamphletIndex', 0
                )
                selected_pamphlets = json.loads(
                    session_attributes.get('selectedPamphlets', '[]')
                )
                logger.debug(
                    'Dialog hook - If there are session attributes, continue - Current pamphlet index: %s, Selected pamphlets: %s, Flow phase: %s',
                    current_pamphlet_index,
                    json.dumps(selected_pamphlets),
                    flow_phase,
                )

                # if current_pamphlet_index == 1-7:
                if int(current_pamphlet_index) <= 7:
                    # UnderstandingSocialSecurity, RetirementBenefits, DisabilityBenefits, SurvivorBenefits, HowWorkAffectsBenefits, BenefitsForChildrenWithDisabilities, WhatEveryWomanShouldKnowAboutSocialSecurity
                    pamphlet_name = self.slot_names[str(current_pamphlet_index)]
                    pamphlet_slot = slots[pamphlet_name]
                    selected_pamphlets = json.loads(
                        session_attributes.get('selectedPamphlets', '[]')
                    )

                    # Get pamphlet value
                    pamphlet_value = ''
                    if pamphlet_slot and 'value' in pamphlet_slot:
                        pamphlet_value = (
                            pamphlet_slot['value'].get('interpretedValue', '').lower()
                        )
                    logger.debug(
                        'Pamphlet name: %s, Pamphlet value: %s, Flow phase: %s, Selected pamphlets: %s',
                        pamphlet_name,
                        pamphlet_value,
                        flow_phase,
                        selected_pamphlets,
                    )
                    # If yes, add pamphlet to selected pamphlets and ask if they want to hear next pamphlet
                    if 'yes' in pamphlet_value.lower():
                        new_index = str(int(current_pamphlet_index) + 1)
                        selected_pamphlets.append(pamphlet_name)
                        selected_pamphlets_json = json.dumps(selected_pamphlets)
                        logger.debug(
                            'Flow phase: %s',
                            flow_phase,
                        )
                        session_attributes.update(
                            {
                                'selectedPamphlets': selected_pamphlets_json,
                                'currentPamphletIndex': new_index,
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='HearNextPamphletChoiceConfirmation',
                            message='Before I get your mailing address, would you like to hear more choices?',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    # If no, move to address intent
                    selected_pamphlets = json.loads(
                        session_attributes.get('selectedPamphlets', '[]')
                    )
                    if 'no' in pamphlet_value.lower():
                        session_attributes.update(
                            {
                                'selectedPamphlets': json.dumps(selected_pamphlets),
                                'flowPhase': 'address',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message='What is your street name?',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Offer next pamphlet
                if 'HearNextPamphletChoiceConfirmation' in slots:
                    pamphlet_slot = slots['HearNextPamphletChoiceConfirmation']
                    pamphlet_confirmation = ''
                    if pamphlet_slot and 'value' in pamphlet_slot:
                        pamphlet_confirmation = (
                            pamphlet_slot['value'].get('interpretedValue', '').lower()
                        )
                    logger.debug(
                        'Hear next pamphlet choice confirmation: %s, Flow phase: %s',
                        pamphlet_confirmation,
                        flow_phase,
                    )
                    slot_name = session_attributes['currentPamphletIndex']
                    pamphlet_name = self.slot_names[slot_name]
                    if 'yes' in pamphlet_confirmation:
                        return self.elicit_slot_response(
                            slot_name=pamphlet_name,
                            message=f'Do you want the pamphlet on {pamphlet_name}?',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Went through all the pamphlets, offer choices again
                if int(current_pamphlet_index) > 7:
                    # There are no pamphlets selected, offer to hear choices again
                    if len(selected_pamphlets) == 0:
                        return self.elicit_slot_response(
                            slot_name='HearPamphletChoicesAgain',
                            message='That was the last one. Would you like to hear those choices again?',
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    if len(selected_pamphlets) > 0 and len(selected_pamphlets) < 7:
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message="Thanks. Now let's get your address. What is your street name?",
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    if len(selected_pamphlets) == 7:
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message="That's all the pamphlets I have to offer. Thanks. Now let's get your address. What's your street name?",
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

            # If pamphlet choices again, reset index and start over
            if 'HearPamphletChoicesAgain' in slots:
                pamphlet_choices_again = slots['HearPamphletChoicesAgain']
                pamphlet_name = self.slot_names[str(current_pamphlet_index)]
                if 'yes' in pamphlet_choices_again:
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',
                            'selectedPamphlets': json.dumps([]),
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name=pamphlet_name,
                        message=f'Do you want the pamphlet on {pamphlet_name}?',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )
                if 'no' in pamphlet_choices_again:
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',
                        }
                    )
                    return self.close_response(
                        session_attributes=session_attributes,
                        intent_name='MainMenu',
                        message="Alright. If you're finished, feel free to hang up. Otherwise, just hang on and I'll take you back to the Main Menu.",
                    )

        if intent_name == 'Address':
            if 'StreetName' in slots:
                street_name = slots['StreetName']
                session_attributes.update(
                    {
                        'streetName': street_name,
                    }
                )
                return self.elicit_slot_response(
                    slot_name='City',
                    message='What is your city?',
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            if 'City' in slots:
                city = slots['City']
                session_attributes.update(
                    {
                        'city': city,
                    }
                )
                return self.elicit_slot_response(
                    slot_name='State',
                    message='What is your state?',
                    session_attributes=session_attributes,
                    intent='ProcessPamphletRequest',
                )

            if 'State' in slots:
                state = slots['State']
                session_attributes.update(
                    {
                        'state': state,
                    }
                )
                return self.elicit_slot_response(
                    slot_name='ZipCode',
                    message='What is your zip code?',
                    session_attributes=session_attributes,
                    intent='ProcessPamphletRequest',
                )

        return self.fulfillment_hook(event)

    def fulfillment_hook(self, event):
        """Handle fulfillment - determine final action based on collected slots"""
        intent_object = self.get_intent(event)
        intent_name = intent_object.get('name', '')
        slots = self.get_slots(event)
        session_attributes = self.get_session_attributes(event)

        logger.debug(
            'Fulfillment hook - Intent: %s, Slots: %s, Session Attributes: %s',
            json.dumps(intent_name),
            json.dumps(slots),
            json.dumps(session_attributes),
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

    def get_intent(self, event):
        """Extract intent from event"""
        return event.get('sessionState', {}).get('intent', {})

    def get_slots(self, event):
        """Extract slots from event"""
        return event.get('sessionState', {}).get('intent', {}).get('slots', {})

    def get_slot_value(self, slots, slot_name):
        """Extract slot value from event"""
        return slots.get(slot_name, '')

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
    return handler_instance.handler(event, context)
