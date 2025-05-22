from typing import Literal

# Voice engine type
VoiceEngine = Literal['standard', 'neural']

"""
Default values for the bots.
You can override this in the individual bot configuration.
"""


class LexDefaults:
    # Session timeout in seconds
    idle_session_ttl_in_seconds: int = 300

    # Confidence threshold for natural language understanding
    nlu_confidence_threshold: float = 0.4

    # Slot elicitation interrupt
    slot_allow_interrupt: bool = True

    # Slot elicitation retries
    slot_retries: int = 3
