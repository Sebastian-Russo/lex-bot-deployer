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
        'Agent': [
            "You'd like to talk to an agent, right?",
            "Let's try again. You'd like to talk to an agent, right?",
            'Sorry. TO talk to an agent, press 1, otherwise press 2.',
        ],
        'Finished': [
            '',
        ],
    }

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
            return self.handle_confirmation_phase(slots, step, session_attrs, intent)

        elif phase == 'completed':
            return self.close_fulfillment(slots)

        return self.delegate(session_attrs, intent)

    ### Phase Handlers ###

    def handle_selection_phase(self, slots, step, session_attrs, intent):
        """Handle selection phase - collect pamphlet slots"""
        # Get the index of the current step
        index = int(step.replace('selection_', ''))

        # Check if index is less than the 7 pamphlet slots
        if index < len(PAMPHLET_SLOTS):
            slot_name = PAMPHLET_SLOTS[index]

            # If the slot is not filled, elicit it with a custom prompt
            if not self.is_slot_filled(slots, slot_name):
                prompt_list = self.prompts.get(slot_name)
                if prompt_list and prompt_list[0]:
                    prompt = prompt_list[0]
                else:
                    prompt = f'Do you want the pamphlet on {self.format_slot_name(slot_name)}?'

                return self.elicit_slot(
                    slot_name,
                    session_attrs,
                    f'selection_{index + 1}',
                    intent,
                    message=prompt,
                )
            else:
                # If the slot is filled, delegate to the next step (ask to hear next pamphlet)
                return self.delegate(
                    self.update_step(session_attrs, f'selection_{index + 1}'), intent
                )
        # All pamphlets processed → move to address collection
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

    def is_slot_filled(self, slots, name):
        """Check if a slot is filled
        If the current slot is not filled, call elicit_slot
        It also sets currentStep to the next step
        """
        return bool(
            slots.get(name) and slots[name].get('value', {}).get('interpretedValue')
        )

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

    def format_slot_name(slot_name):
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', slot_name)

    def elicit_slot(self, slot_name, session_attrs, next_step, intent, message=None):
        """Elicit a slot, optionally with a custom prompt message"""
        response = {
            'sessionState': {
                'dialogAction': {
                    'type': 'ElicitSlot',
                    'slotToElicit': slot_name,
                },
                'sessionAttributes': self.update_step(session_attrs, next_step),
                'intent': {
                    'name': intent['name'],
                    'slots': intent.get('slots'),
                    'state': 'InProgress',
                },
            }
        }

        if message:
            response['messages'] = [
                {
                    'contentType': 'PlainText',
                    'content': message,
                }
            ]

        return response

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

    def get_elicitation_prompt(self, slot_name, attempt=0):
        return

    def elicit_slot_response(
        self, slot_to_elicit, session_attributes, intent_name, slots, attempt=0
    ):
        """
        Build Lex response to elicit a slot with the right prompt.
        """
        prompt_text = self.get_elicitation_prompt(slot_to_elicit, attempt)

        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitSlot', 'slotToElicit': slot_to_elicit},
                'intent': {'name': intent_name, 'slots': slots, 'state': 'InProgress'},
                'sessionAttributes': session_attributes,
            },
            'messages': [{'contentType': 'PlainText', 'content': prompt_text}],
        }


handler_instance = PamphletHandler()


def handler(event, context=None):
    """Lambda handler function"""
    return handler_instance.handler(event, context)
