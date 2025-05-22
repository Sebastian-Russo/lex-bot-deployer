from typing import List, Literal, Mapping, Optional, Union

from attr import dataclass

# Define action types
ActionType = Literal['PhoneTransfer', 'QueueTransfer', 'FlowTransfer', 'Prompt']


@dataclass
class BaseAction:
    """Base action for menu items"""

    type: ActionType

    # Optional fields
    custom_handler: Optional[str] = None  # Lambda ARN if provided


@dataclass
class TransferAction(BaseAction):
    """Base transfer action with optional prompts"""

    pre_transfer_prompt: Optional[str] = None  # Prompt played before transfer


@dataclass(kw_only=True)
class PhoneTransferAction(TransferAction):
    """Transfer to a phone number"""

    type = 'PhoneTransfer'
    phone_number: str  # E.164 format phone number


@dataclass(kw_only=True)
class QueueTransferAction(TransferAction):
    """Transfer to a standard or agent queue"""

    type = 'QueueTransfer'
    queue_arn: str  # Amazon Connect Queue ARN


@dataclass(kw_only=True)
class FlowTransferAction(TransferAction):
    """Transfer to a contact flow"""

    type = 'FlowTransfer'
    contact_flow_arn: str  # Amazon Connect Contact Flow ARN


@dataclass(kw_only=True)
class PromptAction(BaseAction):
    """Play a prompt to the user"""

    type = 'Prompt'
    prompt: str
    hang_up: bool = False


# Union type for all possible actions
MenuAction = Union[
    PhoneTransferAction, QueueTransferAction, FlowTransferAction, PromptAction
]


@dataclass
class MenuItem:
    """Defines an IVR menu item (Associated with a lex intent)"""

    utterances: List[str]  # Phrases associated with this menu item
    action: MenuAction  # Action to take when selected

    confirmation: Optional[str] = None  # Prompt to confirm the intent if provided


@dataclass
class RequiredIntent:
    """Basic intent with utterances and a response"""

    utterances: List[str]
    response: str


@dataclass
class MenuLocale:
    """Locale configuration for the menu bot"""

    locale_id: str
    voice_id: str
    greeting: str  # Initial IVR greeting
    more_prompt: str  # Prompt to ask if caller needs more help
    help: RequiredIntent  # Help intent
    hang_up: RequiredIntent  # Hang up intent (e.g., "no" to more_prompt)
    menu: Mapping[str, MenuItem]  # Menu items defining bot intents and actions


@dataclass
class MenuBot:
    """Top-level menu bot configuration"""

    name: str
    description: str
    locales: List[MenuLocale]
