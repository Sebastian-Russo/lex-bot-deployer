import json
import os
import sys

test_config = {
    'en_US': {
        'langCode': 'en_US',
        'greeting': 'Thank you for calling the non-emergency hotline. How may I help you?',
        'morePrompt': 'Is there anything else I can help you with?',
        'help': "You can say things like, 'I would like to speak to the police department', 'I would like to speak to the fire department', or 'I would like to speak to animal control'.",
        'hangUp': 'Ok, thank you for calling, and have a nice day!',
        'Emergency': {
            'custom_handler': None,
            'prompt': 'Please call 911 immediately. Goodbye.',
            'type': 'Prompt',
            'hang_up': True,
        },
        'PoliceNumber': {
            'custom_handler': None,
            'prompt': 'The police department can be reached at 111 222 4444.',
            'type': 'Prompt',
            'hang_up': False,
        },
        'FireDepartmentNumber': {
            'custom_handler': None,
            'prompt': 'The fire department can be reached at 111 222 5555.',
            'type': 'Prompt',
            'hang_up': None,
        },
        'MayDayInfo': {
            'custom_handler': None,
            'prompt': 'This year we are celebrating May Day on May 1st. The parade starts at 10am. Atlantic Avenue will be closed from 9am to 1pm between 1st and 5th streets.',
            'type': 'Prompt',
            'hang_up': False,
        },
        'PoliceTransfer': {
            'type': 'PhoneTransfer',
            'custom_handler': None,
            'pre_transfer_prompt': 'Please wait while I transfer your call to the police department.',
            'phone_number': '+16462259369',
        },
        'FireDepartment': {
            'type': 'PhoneTransfer',
            'custom_handler': None,
            'pre_transfer_prompt': 'Please wait while I transfer your call to the fire department.',
            'phone_number': '+16462259369',
        },
        'PublicWorks': {
            'type': 'PhoneTransfer',
            'custom_handler': None,
            'pre_transfer_prompt': 'Please wait while I transfer your call to the public works department.',
            'phone_number': '+16462259369',
        },
        'AnimalControl': {
            'custom_handler': None,
            'prompt': 'Ok, I just sent you a text message containing a form link. Please fill out the form so that we can dispatch someone to help you. Have a nice day.',
            'type': 'Prompt',
            'hang_up': None,
        },
        'BuildingDepartment': {
            'type': 'PhoneTransfer',
            'custom_handler': None,
            'pre_transfer_prompt': 'Please wait while I transfer your call to the building department.',
            'phone_number': '+16462259369',
        },
    }
}
os.environ['CONFIG'] = json.dumps(test_config)

# Add the parent directory to sys.path to import the handler module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from index import handler


def run_test():
    # Load the test event from fulfilled.json
    with open(os.path.join(os.path.dirname(__file__), 'fulfilled.json'), 'r') as f:
        event = json.load(f)

    # Call the handler with our test event
    result = handler(event)

    # Print the result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run_test()
