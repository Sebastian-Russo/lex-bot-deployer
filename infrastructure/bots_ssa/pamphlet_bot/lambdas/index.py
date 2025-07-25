"""
Handle pamphlet bot
"""

import json
import logging
import os
import random

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOGGING_LEVEL', 'DEBUG'))


class PamphletHandler:
    """Handle pamphlet bot"""

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
        last_message = session_attributes.get('lastMessage', '')
        logger.debug('Dialog hook')
        logger.debug('Intent: %s', json.dumps(intent_name))
        logger.debug('Slots: %s', json.dumps(slots))
        logger.debug('Flow Phase: %s', json.dumps(flow_phase))
        logger.debug('Session Attributes: %s', json.dumps(session_attributes))

        if intent_name == 'ProcessPamphletRequest':
            logger.debug('ProcessPamphletRequest')
            # Get Session Attributes
            current_pamphlet_index = session_attributes.get(
                'currentPamphletIndex', None
            )

            # flowChange selection, no session attributes, initialize
            if flow_phase == 'selection' and current_pamphlet_index is None:
                logger.debug('Dialog Hook - Initialize Session Attributes')
                pamphlet_slot = slots.get('UnderstandingSocialSecurity', None)
                pamphlet_value = ''

                # If no session attributes, start at the beginning, initialize session attributes
                # Offer first pamphlet
                if 'currentPamphletIndex' not in session_attributes:
                    message = 'Would you like to hear the pamphlet on Understanding Social Security?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',  # add 1 for first pamphlet
                            'flowPhase': 'selection',
                            'selectedPamphlets': json.dumps([]),
                            'lastMessage': message,
                            'lastSlot': 'UnderstandingSocialSecurity',
                        }
                    )
                return self.elicit_slot_response(
                    slot_name='UnderstandingSocialSecurity',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            # flowPhone selection, session attributes, continue
            if flow_phase == 'selection' and current_pamphlet_index is not None:
                pamphlet_slot = slots.get('UnderstandingSocialSecurity', None)
                pamphlet_value = ''
                if pamphlet_slot and 'value' in pamphlet_slot:
                    pamphlet_value = (
                        pamphlet_slot['value'].get('interpretedValue', '').lower()
                    )
                logger.debug('Pamphlet slot: %s', json.dumps(pamphlet_slot))
                logger.debug('Pamphlet value: %s', json.dumps(pamphlet_value))

                current_pamphlet_index = session_attributes.get(
                    'currentPamphletIndex', 0
                )
                selected_pamphlets = json.loads(
                    session_attributes.get('selectedPamphlets', '[]')
                )
                logger.debug('Dialog hook')
                logger.debug('Current pamphlet index: %s', current_pamphlet_index)
                logger.debug('Selected pamphlets: %s', json.dumps(selected_pamphlets))
                logger.debug('Flow phase: %s', flow_phase)

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
                    logger.debug('Pamphlet name: %s', pamphlet_name)
                    logger.debug('Pamphlet value: %s', pamphlet_value)
                    logger.debug('Flow phase: %s', flow_phase)
                    logger.debug('Selected pamphlets: %s', selected_pamphlets)
                    selected_pamphlets = json.loads(
                        session_attributes.get('selectedPamphlets', '[]')
                    )
                    new_index = int(current_pamphlet_index) + 1
                    # If yes they want pamphlet, add pamphlet to selected pamphlets and ask if they want to hear next pamphlet
                    if 'yes' in pamphlet_value.lower():
                        selected_pamphlets.append(pamphlet_name)
                        message = 'Before I get your mailing address, would you like to hear more choices?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'currentPamphletIndex': str(new_index),
                                'selectedPamphlets': json.dumps(selected_pamphlets),
                                'lastMessage': message,
                                'lastSlot': 'HearNextPamphletChoiceConfirmation',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='HearNextPamphletChoiceConfirmation',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    # If no, ask for next pamphlet before moving to address intent
                    if 'no' in pamphlet_value.lower():
                        if len(selected_pamphlets) == 0:
                            message = f'Do you want the pamphlet on {pamphlet_name}?'
                            logger.debug('Message: %s', message)
                            session_attributes.update(
                                {
                                    'lastMessage': message,
                                    'lastSlot': pamphlet_name,
                                }
                            )
                            return self.elicit_slot_response(
                                slot_name=pamphlet_name,
                                message=message,
                                session_attributes=session_attributes,
                                intent=intent_object,
                            )
                        message = 'Before I get your mailing address, would you like to hear more choices?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'currentPamphletIndex': str(new_index),
                                'selectedPamphlets': json.dumps(selected_pamphlets),
                                'lastMessage': message,
                                'lastSlot': 'HearNextPamphletChoiceConfirmation',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='HearNextPamphletChoiceConfirmation',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Went through all the pamphlets, offer choices again
                if int(current_pamphlet_index) > 7:
                    # There are no pamphlets selected, offer to hear choices again
                    if len(selected_pamphlets) == 0:
                        message = 'That was the last pamphlet. Would you like to hear those choices again?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'lastMessage': message,
                                'lastSlot': 'HearAllChoicesAgain',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='HearAllChoicesAgain',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    if len(selected_pamphlets) > 0 and len(selected_pamphlets) < 7:
                        message = "Thanks. Now let's get your address. What is your street name? (1)"
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'StreetName',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    if len(selected_pamphlets) == 7:
                        message = "That's all the pamphlets I have to offer. Thanks. Now let's get your address. What's your street name?"
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'selectedPamphlets': json.dumps(selected_pamphlets),
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'StreetName',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message=message,
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
                        'Hear next pamphlet choice confirmation: %s',
                        pamphlet_confirmation,
                    )
                    logger.debug('Flow phase: %s', flow_phase)
                    slot_name = session_attributes['currentPamphletIndex']
                    pamphlet_name = self.slot_names[slot_name]
                    if 'yes' in pamphlet_confirmation:
                        slots['HearNextPamphletChoiceConfirmation'] = None
                        message = f'Do you want the pamphlet on {pamphlet_name}?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'lastMessage': message,
                                'lastSlot': pamphlet_name,
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name=pamphlet_name,
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )
                    if 'no' in pamphlet_confirmation:
                        slots['HearNextPamphletChoiceConfirmation'] = None
                        message = "Thanks. Now let's get your address. What is your street name? (2)"
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'StreetName',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

            if flow_phase == 'address':
                logger.debug('Flow phase: %s', flow_phase)
                logger.debug('Slots: %s', json.dumps(slots))

                # Extract slot values properly
                street_name_slot = slots.get('StreetName')
                city_slot = slots.get('City')
                state_slot = slots.get('State')
                zip_code_slot = slots.get('ZipCode')

                # Debug the slot values
                logger.debug('StreetName slot: %s', street_name_slot)
                logger.debug('City slot: %s', city_slot)
                logger.debug('State slot: %s', state_slot)
                logger.debug('ZipCode slot: %s', zip_code_slot)

                # Check if ZipCode has a value
                if zip_code_slot and 'value' in zip_code_slot:
                    # All address slots should be provided, format the address
                    street_name_value = (
                        street_name_slot['value'].get('interpretedValue', '')
                        if street_name_slot
                        else ''
                    )
                    city_value = (
                        city_slot['value'].get('interpretedValue', '')
                        if city_slot
                        else ''
                    )
                    state_value = (
                        state_slot['value'].get('interpretedValue', '')
                        if state_slot
                        else ''
                    )
                    zip_code_value = zip_code_slot['value'].get('interpretedValue', '')
                    logger.debug(
                        'Address values - Street: %s, City: %s, State: %s, Zip: %s',
                        street_name_value,
                        city_value,
                        state_value,
                        zip_code_value,
                    )

                    # Format the address
                    full_address = f'{street_name_value}, {city_value}, {state_value}, {zip_code_value}'
                    logger.debug('Formatted address: %s', full_address)

                    # Update session attributes with full address and change flow phase
                    message = f'Is this your address: {full_address}?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'fullAddress': full_address,
                            'flowPhase': 'confirmation',
                            'lastMessage': message,
                            'lastSlot': 'AddressConfirmation',
                        }
                    )
                    # Elicit AddressConfirmation slot
                    return self.elicit_slot_response(
                        slot_name='AddressConfirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Check if we're in address flow and last slot was ZipCode
                # This captures cases where Lex doesn't recognize the input as a valid slot value
                if (
                    flow_phase == 'address'
                    and session_attributes.get('lastSlot') == 'ZipCode'
                    and 'inputTranscript' in event
                ):
                    # Manually capture the user's input as the zip code
                    user_input = event.get('inputTranscript', '')
                    logger.debug(
                        'Manually capturing zip code from input: %s', user_input
                    )

                    if user_input and user_input.strip():
                        # Set the zip code slot value manually
                        if 'slots' not in intent_object:
                            intent_object['slots'] = {}

                        intent_object['slots']['ZipCode'] = {
                            'value': {
                                'originalValue': user_input,
                                'interpretedValue': user_input,
                                'resolvedValues': [user_input],
                            },
                            'shape': 'Scalar',
                        }

                        # Get all the address values
                        street_name_value = (
                            street_name_slot['value'].get('interpretedValue', '')
                            if street_name_slot and 'value' in street_name_slot
                            else intent_object['slots']
                            .get('StreetName', {})
                            .get('value', {})
                            .get('interpretedValue', '')
                        )
                        city_value = (
                            city_slot['value'].get('interpretedValue', '')
                            if city_slot and 'value' in city_slot
                            else intent_object['slots']
                            .get('City', {})
                            .get('value', {})
                            .get('interpretedValue', '')
                        )
                        state_value = (
                            state_slot['value'].get('interpretedValue', '')
                            if state_slot and 'value' in state_slot
                            else intent_object['slots']
                            .get('State', {})
                            .get('value', {})
                            .get('interpretedValue', '')
                        )
                        zip_code_value = user_input

                        logger.debug(
                            'Address values - Street: %s, City: %s, State: %s, Zip: %s',
                            street_name_value,
                            city_value,
                            state_value,
                            zip_code_value,
                        )

                        # Now that we have all address components, format the address and move to confirmation
                        full_address = f'{street_name_value}, {city_value}, {state_value}, {zip_code_value}'
                        logger.debug(
                            'Formatted address from manual input: %s', full_address
                        )

                        # Update session attributes with full address and change flow phase
                        message = f'Is this your address: {full_address}?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'fullAddress': full_address,
                                'flowPhase': 'confirmation',
                                'lastMessage': message,
                                'lastSlot': 'AddressConfirmation',
                            }
                        )
                        # Elicit AddressConfirmation slot
                        return self.elicit_slot_response(
                            slot_name='AddressConfirmation',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                    # Format the address
                    full_address = f'{street_name_value}, {city_value}, {state_value}, {zip_code_value}'
                    logger.debug('Formatted address: %s', full_address)

                    # Update session attributes with full address and change flow phase
                    message = f'Is this your address: {full_address}?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'fullAddress': full_address,
                            'flowPhase': 'confirmation',
                            'lastMessage': message,
                            'lastSlot': 'AddressConfirmation',
                        }
                    )
                    # Elicit AddressConfirmation slot
                    return self.elicit_slot_response(
                        slot_name='AddressConfirmation',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Check if State has a value
                if state_slot and 'value' in state_slot:
                    # State was provided, move to ZipCode
                    state_value = state_slot['value'].get('interpretedValue', '')
                    logger.debug('State value: %s', state_value)
                    message = 'Thanks. What is your zip code?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'address',
                            'lastMessage': message,
                            'lastSlot': 'ZipCode',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='ZipCode',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Check if we're in address flow and last slot was State
                # This captures cases where Lex doesn't recognize the input as a valid slot value
                if (
                    flow_phase == 'address'
                    and session_attributes.get('lastSlot') == 'State'
                    and 'inputTranscript' in event
                ):
                    # Manually capture the user's input as the state
                    user_input = event.get('inputTranscript', '')
                    logger.debug('Manually capturing state from input: %s', user_input)

                    if user_input and user_input.strip():
                        # Set the state slot value manually
                        if 'slots' not in intent_object:
                            intent_object['slots'] = {}

                        intent_object['slots']['State'] = {
                            'value': {
                                'originalValue': user_input,
                                'interpretedValue': user_input,
                                'resolvedValues': [user_input],
                            },
                            'shape': 'Scalar',
                        }

                        # Move to ZipCode
                        message = 'Thanks. What is your zip code?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'ZipCode',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='ZipCode',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Check if City has a value, ask for State
                if city_slot and 'value' in city_slot:
                    # City was provided, move to State
                    city_value = city_slot['value'].get('interpretedValue', '')
                    logger.debug('City value: %s', city_value)
                    message = 'Thanks. What is your state?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'address',
                            'lastMessage': message,
                            'lastSlot': 'State',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='State',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Check if we're in address flow and last slot was City
                # This captures cases where Lex doesn't recognize the input as a valid slot value
                if (
                    flow_phase == 'address'
                    and session_attributes.get('lastSlot') == 'City'
                    and 'inputTranscript' in event
                ):
                    # Manually capture the user's input as the city
                    user_input = event.get('inputTranscript', '')
                    logger.debug('Manually capturing city from input: %s', user_input)

                    if user_input and user_input.strip():
                        # Set the city slot value manually
                        if 'slots' not in intent_object:
                            intent_object['slots'] = {}

                        intent_object['slots']['City'] = {
                            'value': {
                                'originalValue': user_input,
                                'interpretedValue': user_input,
                                'resolvedValues': [user_input],
                            },
                            'shape': 'Scalar',
                        }

                        # Move to State
                        message = 'Thanks. What is your state?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'State',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='State',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Check if StreetName has a value, ask for City
                if street_name_slot and 'value' in street_name_slot:
                    # Street name was provided, move to City
                    street_name_value = street_name_slot['value'].get(
                        'interpretedValue', ''
                    )
                    logger.debug('Street name value: %s', street_name_value)
                    message = 'Thanks. What is your city?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'address',
                            'lastMessage': message,
                            'lastSlot': 'City',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='City',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

                # Check if we're in address flow and last slot was StreetName
                # This captures cases where Lex doesn't recognize the input as a valid slot value
                if (
                    flow_phase == 'address'
                    and session_attributes.get('lastSlot') == 'StreetName'
                    and 'inputTranscript' in event
                ):
                    # Manually capture the user's input as the street name
                    user_input = event.get('inputTranscript', '')
                    logger.debug(
                        'Manually capturing street name from input: %s', user_input
                    )

                    if user_input and user_input.strip():
                        # Set the street name slot value manually
                        if 'slots' not in intent_object:
                            intent_object['slots'] = {}

                        intent_object['slots']['StreetName'] = {
                            'value': {
                                'originalValue': user_input,
                                'interpretedValue': user_input,
                                'resolvedValues': [user_input],
                            },
                            'shape': 'Scalar',
                        }

                        # Move to City
                        message = 'Thanks. What is your city?'
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'lastMessage': message,
                                'lastSlot': 'City',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='City',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # Fallback: If we get here, start with street name
                message = (
                    "Thanks. Now let's get your address. What is your street name? (3)"
                )
                logger.debug('Message: %s', message)
                session_attributes.update(
                    {
                        'flowPhase': 'address',
                        'lastMessage': message,
                        'lastSlot': 'StreetName',
                    }
                )
                return self.elicit_slot_response(
                    slot_name='StreetName',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

            if flow_phase == 'confirmation':
                logger.debug('Flow phase: %s', flow_phase)
                logger.debug('Slots: %s', slots)
                logger.debug('Session Attributes: %s', json.dumps(session_attributes))

                # Extract AddressConfirmation slot
                confirmation_slot = slots.get('AddressConfirmation')
                logger.debug('AddressConfirmation: %s', confirmation_slot)

                # Check if AddressConfirmation has a value
                if confirmation_slot and 'value' in confirmation_slot:
                    confirmation_value = (
                        confirmation_slot['value'].get('interpretedValue', '').lower()
                    )
                    logger.debug('AddressConfirmation value: %s', confirmation_value)

                    # Check selectedPamphlets
                    selected_pamphlets = json.loads(
                        session_attributes.get('selectedPamphlets', '[]')
                    )
                    logger.debug('Selected pamphlets: %s', selected_pamphlets)

                    # If no pamphlets selected, prompt to select pamphlets again
                    if not selected_pamphlets:
                        message = "You haven't selected any pamphlets. Let's start again. Would you like to hear the pamphlet on Understanding Social Security?"
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'selection',
                                'currentPamphletIndex': '1',
                                'fullAddress': '',  # Clear address since we're restarting
                                'lastMessage': message,
                                'lastSlot': 'UnderstandingSocialSecurity',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='UnderstandingSocialSecurity',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                    # If user confirms the address
                    if 'yes' in confirmation_value:
                        # Ensure session_attributes are preserved
                        session_attributes.update(
                            {  # Keep for clarity in fulfillment
                                'flowPhase': 'confirmation'
                            }
                        )
                        # Delegate to FulfillmentCodeHook
                        return self.delegate_response(
                            session_attributes=session_attributes,
                            intent_object=intent_object,
                        )
                    # If user denies the address
                    if 'no' in confirmation_value:
                        # Reset address slots and flow phase
                        intent_object['slots']['StreetName'] = None
                        intent_object['slots']['City'] = None
                        intent_object['slots']['State'] = None
                        intent_object['slots']['ZipCode'] = None
                        message = "Okay, let's try again. What is your street name?"
                        logger.debug('Message: %s', message)
                        session_attributes.update(
                            {
                                'flowPhase': 'address',
                                'fullAddress': '',  # Clear stored address
                                'lastMessage': message,
                                'lastSlot': 'StreetName',
                            }
                        )
                        return self.elicit_slot_response(
                            slot_name='StreetName',
                            message=message,
                            session_attributes=session_attributes,
                            intent=intent_object,
                        )

                # If AddressConfirmation slot is not yet filled, elicit it again
                full_address = session_attributes.get('fullAddress', '')
                if not full_address:
                    logger.debug('No fullAddress found, restarting address collection')
                    message = "Okay, let's try again. What is your street name?"
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'address',
                            'fullAddress': '',
                            'lastMessage': message,
                            'lastSlot': 'StreetName',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='AddressConfirmation',  ##
                        message=f'Is this your address: {full_address}?',
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

            # If pamphlet choices again, reset index and start over
            if (
                'HearAllChoicesAgain' in slots
                and slots['HearAllChoicesAgain'] is not None
            ):
                pamphlet_choices_again = (
                    slots['HearAllChoicesAgain']['value']
                    .get('interpretedValue', '')
                    .lower()
                )
                logger.debug('HearAllChoicesAgain value: %s', pamphlet_choices_again)
                if (
                    pamphlet_choices_again is not None
                    and 'yes' in pamphlet_choices_again
                ):
                    message = "You haven't selected any pamphlets. Let's start again. Would you like to hear the pamphlet on Understanding Social Security?"
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',
                            'selectedPamphlets': json.dumps([]),
                            'flowPhase': 'selection',
                            'lastMessage': message,
                            'lastSlot': 'UnderstandingSocialSecurity',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='UnderstandingSocialSecurity',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )
                if (
                    pamphlet_choices_again is not None
                    and 'no' in pamphlet_choices_again
                ):
                    message = "Alright. If you're finished, feel free to hang up. Otherwise, just hang on and I'll take you back to the Main Menu."
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'currentPamphletIndex': '1',
                            'lastMessage': message,
                            'lastSlot': 'MainMenu',
                        }
                    )
                    return self.close_response(
                        session_attributes=session_attributes,
                        intent_name='MainMenu',
                        message=message,
                    )

        elif intent_name == 'Skip':
            logger.debug('Skip Intent')
            # Invalid skip - not in selection phase
            if flow_phase != 'selection':
                logger.debug('Skip intent triggered outside selection phase')
                return self.close_response(
                    session_attributes=session_attributes,
                    intent_name=intent_name,
                    message=f'Sorry, you can only skip pamphlets while selecting them. {last_message}',
                )
            # Grab sesion attributes
            current_index = int(session_attributes.get('currentPamphletIndex', 1))
            selected_pamphlets = json.loads(
                session_attributes.get('selectedPamphlets', '[]')
            )
            # Increment pamphlet index
            current_index += 1
            session_attributes['currentPamphletIndex'] = str(current_index)
            logger.debug('Updated currentPamphletIndex to %s', current_index)
            # If within pamphlet selection
            if current_index <= 7:
                next_pamphlet = self.slot_names[str(current_index)]
                intent_object['name'] = (
                    'ProcessPamphletRequest'  # Switch back to main intent
                )
                message = f'Would you like to hear the pamphlet on {self._format_pamphlet_name(next_pamphlet)}?'
                logger.debug('Message: %s', message)
                session_attributes.update(
                    {
                        'flowPhase': 'selection',
                        'lastMessage': message,
                        'lastSlot': next_pamphlet,
                    }
                )
                return self.elicit_slot_response(
                    slot_name=next_pamphlet,
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )
            # If at last pamphlet
            # if current_index == 7:
            #     intent_object['name'] = 'ProcessPamphletRequest' # Switch back to main intent
            # session_attributes.update(
            #     {
            #         'flowPhase': 'selection',
            #         'lastMessage': 'That was the last one. Would you like to hear those choices again?',
            #         'lastSlot': 'HearAllChoicesAgain',
            #     }
            # )
            #     return self.elicit_slot_response(
            #         slot_name='HearAllChoicesAgain',
            #         message='That was the last one. Would you like to hear those choices again?',
            #         session_attributes=session_attributes,
            #         intent=intent_object,
            #     )
            else:
                if not selected_pamphlets:
                    intent_object['name'] = 'ProcessPamphletRequest'
                    message = 'That was the last one. Would you like to hear those choices again?'
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'selection',
                            'lastMessage': message,
                            'lastSlot': 'HearAllChoicesAgain',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='HearAllChoicesAgain',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )
                else:
                    message = "Thanks. Now let's get your address. What is your street name? (4)"
                    logger.debug('Message: %s', message)
                    session_attributes.update(
                        {
                            'flowPhase': 'address',
                            'lastMessage': message,
                            'lastSlot': 'StreetName',
                        }
                    )
                    return self.elicit_slot_response(
                        slot_name='StreetName',
                        message=message,
                        session_attributes=session_attributes,
                        intent=intent_object,
                    )

        elif intent_name == 'Repeat':
            logger.debug('RepeatRequest Intent')
            last_message = session_attributes.get('lastMessage', '')
            last_slot = session_attributes.get('lastSlot', '')
            logger.debug('Last message: %s', last_message)
            logger.debug('Last slot: %s', last_slot)

            # Valid slots for re-elicitation
            valid_slots = list(self.slot_names.values()) + [
                'HearNextPamphletChoiceConfirmation',
                'HearAllChoicesAgain',
                'StreetName',
                'City',
                'State',
                'ZipCode',
                'AddressConfirmation',
            ]

            # If valid last message and slot
            if last_message and last_slot and last_slot in valid_slots:
                intent_object['name'] = (
                    'ProcessPamphletRequest'  # Switch back to main intent
                )
                message = f'Sure, let me repeat that: {last_message}'
                logger.debug('Message: %s', message)

                # Preserve the current flow phase instead of always setting to 'selection'
                current_flow_phase = session_attributes.get('flowPhase', 'selection')
                session_attributes.update(
                    {
                        'flowPhase': current_flow_phase,
                        'lastMessage': message,
                        'lastSlot': last_slot,
                    }
                )
                return self.elicit_slot_response(
                    slot_name=last_slot,
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )
            # If no valid last message or slot
            else:
                logger.warning(
                    'No valid last message or slot to repeat: message=%s, slot=%s',
                    last_message,
                    last_slot,
                )
                intent_object['name'] = 'ProcessPamphletRequest'
                message = "Sorry, there's nothing to repeat yet. Would you like a pamphlet on Understanding Social Security?"
                session_attributes.update(
                    {
                        'flowPhase': 'selection',
                        'lastMessage': message,
                        'lastSlot': 'UnderstandingSocialSecurity',
                    }
                )
                return self.elicit_slot_response(
                    slot_name='UnderstandingSocialSecurity',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )

        elif intent_name == 'ReturnToMenu':
            logger.debug('ReturnToMenu Intent')
            session_attributes = self.get_session_attributes(event)
            last_message = session_attributes.get('lastMessage', '')
            last_slot = session_attributes.get('lastSlot', '')
            logger.debug('Last message: %s', last_message)
            logger.debug('Last slot: %s', last_slot)

            confirmation_slot = slots.get('ConfirmationMainMenu')
            confirmation_value = ''
            logger.debug('ConfirmationMainMenu slot: %s', confirmation_slot)

            # Check slot confirmation
            if confirmation_slot and 'value' in confirmation_slot:
                confirmation_value = (
                    confirmation_slot['value'].get('interpretedValue', '').lower()
                )
                logger.debug('ConfirmationMainMenu slot: %s', confirmation_value)

            # If None or empty, confirm return to menu
            if confirmation_value is None or confirmation_value == '':
                logger.debug('ConfirmationMainMenu is empty')
                message = 'Are you sure you want to return to the main menu?'
                return self.elicit_slot_response(
                    slot_name='ConfirmationMainMenu',
                    message=message,
                    session_attributes=session_attributes,
                    intent=intent_object,
                )
            # If No, return to last slot and intent
            elif confirmation_value.lower() == 'no':
                # Return to last slot and intent
                logger.debug('ConfirmationMainMenu is No')
                current_flow_phase = session_attributes.get('flowPhase', 'selection')

                # Create a new intent object for ProcessPamphletRequest
                process_intent = {'name': 'ProcessPamphletRequest', 'slots': {}}

                # Update session attributes
                session_attributes.update(
                    {
                        'flowPhase': current_flow_phase,
                        'lastMessage': last_message,
                        'lastSlot': last_slot,
                    }
                )

                # Return to the previous slot in the ProcessPamphletRequest intent
                return self.elicit_slot_response(
                    slot_name=last_slot,
                    message=last_message,
                    session_attributes=session_attributes,
                    intent=process_intent,  # Use the new intent object
                )
            # If Yes, clear session and close
            elif confirmation_value.lower() == 'yes':
                logger.debug('ConfirmationMainMenu is Yes')
                session_attributes.clear()
                return self.close_response(
                    session_attributes=session_attributes,
                    intent_name=intent_name,
                    message='Returning to the main menu.',
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

        # Check if we're in the address flow phase and we should redirect back to dialog_hook
        # This prevents premature fulfillment when we're still collecting address information
        flow_phase = session_attributes.get('flowPhase', '')
        if flow_phase == 'address' and not session_attributes.get('fullAddress'):
            logger.debug(
                'In address flow phase but address collection not complete, redirecting to dialog_hook'
            )
            return self.dialog_hook(event)

        if intent_name == 'ProcessPamphletRequest':
            # Extract session attributes
            full_address = session_attributes.get('fullAddress', '')
            selected_pamphlets = json.loads(
                session_attributes.get('selectedPamphlets', '[]')
            )
            logger.debug('Full address: %s', full_address)
            logger.debug('Selected pamphlets: %s', selected_pamphlets)

            # Check if required data is present
            if not full_address or not selected_pamphlets:
                logger.debug(
                    'Missing fullAddress or selectedPamphlets, closing with error'
                )
                return self.close_response(
                    session_attributes=session_attributes,
                    intent_name=intent_name,
                    message='Sorry, there was an issue with your request. Please try again. Missing address or pamphlets.',
                )

            # Simulate API call with 90% success rate
            api_success = random.random() < 0.9  # 90% chance of success
            logger.debug(
                'Mock API call result: %s', 'Success' if api_success else 'Failure'
            )

            # If mock API call is successful, close the conversation
            if api_success:
                # Format pamphlet list for user-friendly response
                formatted_pamphlets = self._format_pamphlet_list(selected_pamphlets)
                return self.close_response(
                    session_attributes=session_attributes,
                    intent_name=intent_name,
                    message=f"All set. I've put your order through, and you should receive the pamphlets, {formatted_pamphlets}, in the mail within two weeks.",
                )
            else:
                return self.close_response(
                    session_attributes=session_attributes,
                    intent_name=intent_name,
                    message='Sorry, there was an issue processing your request. Please try again later. Mock API call fail simulated.',
                )

        elif intent_name == 'Skip':
            logger.debug('Skip intent in fulfillment hook')
            return self.close_response(
                session_attributes=session_attributes,
                intent_name=intent_name,
                message='Moving on.',
            )

        elif intent_name == 'Repeat':
            logger.warning('Repeat intent reached fulfillment_hook unexpectedly')
            flow_phase = session_attributes.get('flowPhase', 'selection')
            message = "Sorry, I didn't catch that. Let's continue where we left off."
            default_slot = (
                'UnderstandingSocialSecurity'
                if flow_phase == 'selection'
                else 'StreetName'
                if flow_phase == 'address'
                else 'AddressConfirmation'
            )
            session_attributes.update(
                {'lastMessage': message, 'lastSlot': default_slot}
            )
            # Set intent to main intent, return to the main flow
            intent_object['name'] = 'ProcessPamphletRequest'
            return self.elicit_slot_response(
                slot_name=default_slot,
                message=message,
                session_attributes=session_attributes,
                intent=intent_object,
            )
        elif intent_name == 'ReturnToMenu':
            return self.close_response(
                session_attributes=session_attributes,
                intent_name=intent_name,
                message='Returning to the main menu.',
            )
        else:
            logger.debug('Unknown intent: %s', intent_name)
            return self.close_response(
                session_attributes=session_attributes,
                intent_name=intent_name,
                message="Sorry, I didn't understand that request. Intent failed.",
            )

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

    ### Helper functions to format ###

    def _format_pamphlet_name(self, pamphlet):
        """Format a single pamphlet name for user-friendly prompts"""
        readable_names = {
            'UnderstandingSocialSecurity': 'Understanding Social Security',
            'RetirementBenefits': 'Retirement Benefits',
            'DisabilityBenefits': 'Disability Benefits',
            'SurvivorBenefits': 'Survivor Benefits',
            'HowWorkAffectsBenefits': 'How Work Affects Benefits',
            'BenefitsForChildrenWithDisabilities': 'Benefits for Children with Disabilities',
            'WhatEveryWomanShouldKnowAboutSocialSecurity': 'What Every Woman Should Know About Social Security',
        }
        return readable_names.get(pamphlet, pamphlet)

    def _format_pamphlet_list(self, pamphlets):
        """Format pamphlet list into a user-friendly string"""
        if not pamphlets:
            return 'none'
        # Convert slot names to readable titles
        readable_names = {
            'UnderstandingSocialSecurity': 'Understanding Social Security',
            'RetirementBenefits': 'Retirement Benefits',
            'DisabilityBenefits': 'Disability Benefits',
            'SurvivorBenefits': 'Survivor Benefits',
            'HowWorkAffectsBenefits': 'How Work Affects Benefits',
            'BenefitsForChildrenWithDisabilities': 'Benefits for Children with Disabilities',
            'WhatEveryWomanShouldKnowAboutSocialSecurity': 'What Every Woman Should Know About Social Security',
        }
        formatted = [readable_names.get(pamphlet, pamphlet) for pamphlet in pamphlets]
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f'{formatted[0]} and {formatted[1]}'
        else:
            return f'{", ".join(formatted[:-1])}, and {formatted[-1]}'

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
