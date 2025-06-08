import json
import logging
import os
import re

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))

# Order of pamphlet slots
PAMPHLET_SLOTS = [
    'UnderstandingSocialSecurity',
    'RetirementBenefits',
    'DisabilityBenefits',
    'SurvivorBenefits',
    'HowWorkAffectsBenefits',
    'BenefitsForChildrenWithDisabilities',
    'WhatEveryWomanShouldKnowAboutSocialSecurity',
]

ADDRESS_STEPS = {
    'address_street': 'StreetName',
    'address_city': 'City',
    'address_state': 'State',
    'address_zip': 'ZipCode',
}


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

    prompts = {
        # Pamphlet Selection Prompts
        'UnderstandingSocialSecurity': [
            'Would you like the pamphlet on Understanding Social Security?',
        ],
        'RetirementBenefits': [
            'Do you want a pamphlet on Retirement Benefits?',
        ],
        'DisabilityBenefits': [
            'Do you want a pamphlet on Disability Benefits?',
        ],
        'SurvivorBenefits': [
            'Do you want a pamphlet on Survivor Benefits?',
        ],
        'HowWorkAffectsBenefits': [
            'Do you want a pamphlet on How Work Affects Benefits?',
        ],
        'BenefitsForChildrenWithDisabilities': [
            'Do you want a pamphlet on Benefits for Children with Disabilities?',
        ],
        'WhatEveryWomanShouldKnowAboutSocialSecurity': [
            'Do you want a pamphlet on What Every Woman Should Know About Social Security?',
        ],
        # Next pamphlet choice confirmation
        'HearNextPamphletChoiceConfirmation': [
            'Before I get your mailing address, would you like to hear more choices?',
        ],
        # Hear all pamphlet choices again
        'HearAllChoicesAgain': [
            'That was the last one. Would you like to hear those choices again?',
        ],
        # Address Prompts
        'StreetName': [
            'What is your street name?',
        ],
        'City': [
            'What is your city?',
        ],
        'State': [
            'What is your state?',
        ],
        'ZipCode': [
            'What is your zip code?',
        ],
        # Agent Prompt
        'Agent': [
            "You'd like to talk to an agent, right?",
            "Let's try again. You'd like to talk to an agent, right?",
            'Sorry. TO talk to an agent, press 1, otherwise press 2.',
        ],
        # Confirmation Prompt
        'Finished': [
            '',
        ],
    }
    # Before I get your mailing address, would you like to hear more choices?

    # end pamphlets (0 selected)
    # That was the last one. Would you like to hear those choices again?

    # end pamphlets (less than 7 pamphlets selected)
    # Thanks. Now let's get your address.

    # end pamphlets (7 pamphlets selected)
    # That's all the pamphlets I have to offer. Thanks. Now let's get your address.

    def dialog_hook(self, event):
        """Handle dialog code hook - controls conditional slot collection"""

        session = event.get('sessionState', {})
        intent = session.get('intent', {})
        session_attrs = session.get('sessionAttributes') or {}
        slots = intent.get('slots', {})

        phase = session_attrs.get('flowPhase', 'selection')
        step = session_attrs.get('currentStep', 'selection_0')

        if phase == 'selection':
            return self.handle_selection_phase(slots, step, session_attrs, intent)

        elif phase == 'address':
            return self.handle_address_phase(slots, step, session_attrs, intent)

        elif phase == 'confirmation':
            return self.handle_confirmation_phase(step, session_attrs, intent)

        elif phase == 'completed':
            return self.close_fulfillment(slots)

        return self.delegate(session_attrs, intent)

    ### Phase Handlers ###

    def handle_selection_phase(self, slots, step, session_attrs, intent):
        """Handle selection phase - collect pamphlet slots"""
        logger.debug('intent: %s', intent.get('name'))
        logger.debug('step: %s', step)
        logger.debug('slots: %s', slots)
        logger.debug('session_attrs: %s', session_attrs)
        # Get the index of the current step
        index = int(step.replace('selection_', ''))

        # Checking for confirmation to hear next pamphlet
        if step.startswith('selection_confirm_'):
            previous_index = index - 1
            confirmation_slot = 'HearNextPamphletChoiceConfirmation'

            # If confirmation not filled yet, elicit it
            if not self.is_slot_filled(slots, confirmation_slot):
                prompt = self.prompts.get(
                    confirmation_slot, ['Would you like to hear more choices?']
                )[0]
                return self.elicit_slot(
                    confirmation_slot,
                    session_attrs,
                    f'selection_confirm_{index}',
                    intent,
                    message=prompt,
                )

            # If confirmation filled, branch accordingly
            elif slots[confirmation_slot]['value']['interpretedValue'].lower() in [
                'yes',
                'y',
            ]:
                # yes, move to next pamphlet
                return self.delegate(
                    self.update_step(session_attrs, f'selection_{index}'), intent
                )
            else:
                # no, move to address collection
                return self.delegate(
                    self.update_phase(session_attrs, 'address', 'address_street'),
                    intent,
                )

        # Check if index is less than the 7 pamphlet slots
        if index < len(PAMPHLET_SLOTS):
            slot_name = PAMPHLET_SLOTS[index]

            # If the slot is not filled, elicit it with a custom prompt
            if not self.is_slot_filled(slots, slot_name):
                slot_title = self.format_slot_name(slot_name)
                prompt = self.prompts.get(
                    slot_name, [f'Do you want the pamphlet on {slot_title}?']
                )[0]
                return self.elicit_slot(
                    slot_name,
                    session_attrs,
                    f'selection_{index}',
                    intent,
                    message=prompt,
                )
            else:
                # After answering about a pamphlet, ask if they want more
                return self.delegate(
                    self.update_step(session_attrs, f'selection_confirm_{index + 1}'),
                    intent,
                )

        # End of list: check if any pamphlet was selected
        if not any(self.is_slot_selected(slots, slot) for slot in PAMPHLET_SLOTS):
            # If "HearAllChoicesAgain" not filled yet, ask it
            if not self.is_slot_selected(slots, 'HearAllChoicesAgain'):
                prompt = self.prompts.get(
                    'HearAllChoicesAgain',
                    ['Would you like to hear those choices again?'],
                )[0]
                return self.elicit_slot(
                    'HearAllChoicesAgain',
                    session_attrs,
                    'selection_repeat_confirm',
                    intent,
                    message=prompt,
                )

            # If user says yes, reset all pamphlet slots and start over
            if slots['HearAllChoicesAgain']['value']['interpretedValue'].lower() in [
                'yes',
                'y',
            ]:
                for slot in PAMPHLET_SLOTS:
                    if slot in intent['slots']:
                        intent['slots'][slot]['value'] = None
                return self.delegate(
                    self.update_step(session_attrs, 'selection_0'), intent
                )
            else:
                return self.delegate(
                    self.update_phase(session_attrs, 'address', 'address_street'),
                    intent,
                )
        else:
            # If at least one pamphlet selected, proceed to address
            return self.delegate(
                self.update_phase(session_attrs, 'address', 'address_street'), intent
            )

    def handle_address_phase(self, slots, step, session_attrs, intent):
        """Handle address phase - collect address slots"""
        steps = list(ADDRESS_STEPS.keys())
        current_slot = ADDRESS_STEPS.get(step)
        current_index = steps.index(step)

        # if the current slot is not filled, elicit it
        if not self.is_slot_filled(slots, current_slot):
            return self.elicit_slot(
                current_slot,
                session_attrs,
                steps[min(current_index + 1, len(steps) - 1)],
                intent,
            )

        # if the current step is the last address step, delegate to confirmation phase
        if step == 'address_zip':
            return self.delegate(
                self.update_phase(session_attrs, 'confirmation', 'confirmation_start'),
                intent,
            )
        # otherwise, delegate to the next step
        else:
            return self.delegate(
                self.update_step(session_attrs, steps[current_index + 1]), intent
            )

    def handle_confirmation_phase(self, step, session_attrs, intent):
        """Handle confirmation phase - collect address slots"""
        if step == 'confirmation_start':
            return self.elicit_slot(
                'Finished', session_attrs, 'confirmation_done', intent
            )
        elif step == 'confirmation_done':
            return self.delegate(
                self.update_phase(session_attrs, 'completed', 'done'), intent
            )

    def close_fulfillment(self, slots):
        """Close fulfillment"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {
                    'name': 'ProcessPamphletRequest',
                    'state': 'Fulfilled',
                    'slots': slots,
                },
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'Thank you! Your pamphlets will be mailed shortly.',
                }
            ],
        }

    ### Helpers ###

    def is_slot_filled(self, slots, slot_name):
        """Check if a slot is filled"""
        return (
            slot_name in slots
            and slots[slot_name] is not None
            and 'value' in slots[slot_name]
            and slots[slot_name]['value'] is not None
            and 'interpretedValue' in slots[slot_name]['value']
        )

    def is_slot_selected(self, slots, slot_name):
        """Return True if slot is filled and user said yes"""
        slot = slots.get(slot_name)
        if not slot or 'value' not in slot or not slot['value']:
            return False
        return slot['value']['interpretedValue'].lower() in ['yes', 'y']

    def update_phase(self, session_attrs, new_phase, new_step):
        """Update the current phase and step"""
        session_attrs.update(
            {
                'flowPhase': new_phase,
                'currentStep': new_step,
            }
        )
        return session_attrs

    def update_step(self, session_attrs, new_step):
        """Update the current step"""
        session_attrs['currentStep'] = new_step
        return session_attrs

    def format_slot_name(self, slot_name):
        """Reformats slot name to be more readable"""
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', slot_name)

    def elicit_slot(self, slot_name, session_attrs, next_step, intent, message=None):
        """Elicit a slot with an optional custom prompt"""
        msg = {'plainTextMessage': {'value': message}} if message else None

        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_name},
                'sessionAttributes': self.update_step(session_attrs, next_step),
                'intent': {
                    'name': intent['name'],
                    'slots': intent.get('slots'),
                    'state': 'InProgress',
                },
            },
            'messages': [msg] if msg else [],
        }

    def delegate(self, session_attrs, intent):
        """Delegate to Lex"""
        return {
            'sessionState': {
                'dialogAction': {'type': 'Delegate'},
                'sessionAttributes': session_attrs,
                'intent': {
                    'name': intent['name'],
                    'slots': intent.get('slots'),
                    'state': 'InProgress',
                },
            }
        }


handler_instance = PamphletHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
