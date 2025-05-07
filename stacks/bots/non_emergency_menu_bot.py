from constructs import Construct
from ..constructs.menu_bot.menu_bot import MenuBot
from ..bots.utterances.help_utterances import HELP_UTTERANCES
from typing import Optional

# Saul Goodman Hotline
# TODO: Change Me
TEST_NUMBER = '+15055034455'

class NonEmergencyMenuBot(Construct):
    """
    Demonstrates how to implement a lex menu bot which can route to numbers and provide information
    """
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        description: Optional[str] = None,
        role=None,
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Example: Create a custom handler for the animal control fulfillment
        # i.e. send a web form to capture additional information
        # animal_control_handler = None

        MenuBot(
            self, 'NonEmergency',
            prefix=prefix,
            connect_instance_arn=connect_instance_arn,
            description=description,
            role=role,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            nlu_confidence_threshold=nlu_confidence_threshold,
            log_group=log_group,
            audio_bucket=audio_bucket,
            include_sample_flow=True,
            locales=[
                {
                    "locale_id": "en_US",
                    "voice_id": "Joanna",
                    "greeting": "Thank you for calling the non-emergency hotline. How may I help you?",
                    "more_prompt": "Is there anything else I can help you with?",
                    "help": {
                        "utterances": HELP_UTTERANCES,
                        "response": "You can say things like, 'I would like to speak to the police department', 'I would like to speak to the fire department', or 'I would like to speak to animal control'.",
                    },
                    "hang_up": {
                        "utterances": ["No", "I dont need anything else", "I am done", "Goodbye"],
                        "response": "Ok, thank you for calling, and have a nice day!",
                    },
                    "menu": {
                        "Emergency": {
                            "utterances": [
                                "This is an emergency",
                                "I am injured",
                                "Someone else is injured",
                                "I am in danger",
                                "I am having a heart attack",
                            ],
                            "action": {
                                "type": "Prompt",
                                "prompt": "Please call 911 immediately. Goodbye.",
                                "hangUp": True,
                            },
                        },
                        # Informational
                        "PoliceNumber": {
                            "utterances": ["What is the number for the police department?", "What is the the cops phone number?"],
                            "action": {
                                "type": "Prompt",
                                "prompt": "The police department can be reached at 111 222 4444.",
                            },
                        },
                        "FireDepartmentNumber": {
                            "utterances": [
                                "What is the number for the fire department?",
                                "What is the the fire department phone number?",
                            ],
                            "action": {
                                "type": "Prompt",
                                "prompt": "The fire department can be reached at 111 222 5555.",
                            },
                        },
                        # FAQ style example for city info
                        "MayDayInfo": {
                            "utterances": [
                                "When are we celebrating May Day?",
                                "Is the city doing a May Day event this year?",
                                "What is the schedule for May Day?",
                            ],
                            "action": {
                                "type": "Prompt",
                                "prompt": "This year we are celebrating May Day on May 1st. The parade starts at 10am. Atlantic Avenue will be closed from 9am to 1pm between 1st and 5th streets.",
                            },
                        },
                        # Transfers
                        "PoliceTransfer": {
                            "utterances": [
                                "I would like to speak to the police department",
                                "The police department please",
                                "I have a noise complaint",
                                "My neighbors music is too loud",
                                "I would like to report vandalism",
                                "I want to report a loiterer",
                                "I want to report suspicious activity",
                                "I am ok, but I was involved in a traffic accident",
                                "I was involved in a traffic accident, everyone is ok",
                                "I would like to report stolen property",
                                "I would like to report a theft",
                                "Someone stole my car",
                                "Someone stole my bike",
                                "Someone stole the tools from my truck",
                                "I want to report a scam",
                                "I want to report a fraud",
                                "I have a trespasser on my property",
                                "I want to report a break-in",
                                "I want to report an abandoned vehicle",
                            ],
                            "confirmation": "It sounds like I need to transfer you to the police department, does that sound right?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Please wait while I transfer your call to the police department.",
                            },
                        },
                        "FireDepartment": {
                            "utterances": [
                                "I need information about fire safety and prevention",
                                "I need help with my smoke detector",
                                "My cat is stuck in a tree",
                                "I need a copy of a fire incident report",
                                "I need a permit for a controlled burn",
                                "I need an outdoor burning permit",
                                "I want to report a problem with a fire hydrant",
                                "I have a question about fireworks regulations",
                                "I want to report a fire lane violation",
                                "I want to report a non-hazardous material spill",
                                "Schedule a fire station tour",
                                "I want to schedule a fire safety inspection",
                                "I am locked out of a building",
                            ],
                            "confirmation": "It sounds like I need to transfer you to the fire department, do you agree?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Please wait while I transfer your call to the fire department.",
                            },
                        },
                        "PublicWorks": {
                            "utterances": [
                                "I need to report a pothole",
                                "I need to report a streetlight outage",
                                "I need to report a damaged sidewalk",
                                "I need to report a blocked storm drain",
                            ],
                            "confirmation": "I think I transfer you to the public works department, does that sound right?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Please wait while I transfer your call to the public works department.",
                            },
                        },
                        "AnimalControl": {
                            "utterances": [
                                "I have a stray animal in my yard",
                                "The stray cats in my neighborhood are out of control",
                                "There is a cow roaming in my neighborhood",
                                "There is a horse on my street",
                                "There is a dead possum on my street",
                                "Somebody hit a deer with their car",
                            ],
                            "confirmation": "It sounds like you need to report an issue to Animal Control, does that sound right?",
                            "action": {
                                "type": "Prompt",
                                "prompt": "Ok, I just sent you a text message containing a form link. Please fill out the form so that we can dispatch someone to help you. Have a nice day.",
                                "hangUp": True,
                                # Associate the custom handler here
                                # "customHandler": animal_control_handler.function_arn if animal_control_handler else None
                            },
                        },
                        "BuildingDepartment": {
                            "utterances": [
                                "I dont think the construction on my street has a permit",
                                "My building is not safe to live in",
                                "My landlord is not fixing my apartment",
                            ],
                            "confirmation": "It sounds like I need to transfer you to the building department, does that sound right?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Please wait while I transfer your call to the building department.",
                            },
                        },
                    },
                    # Required fallback intent
                    "fallback_intent": {
                        "name": "FallbackIntent",
                        "description": "Default intent when no other intent matches",
                        "parentIntentSignature": "AMAZON.FallbackIntent",
                        "utterances": []
                    }
                },
            ],
        )