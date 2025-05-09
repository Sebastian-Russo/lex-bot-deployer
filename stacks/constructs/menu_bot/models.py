from typing import Dict, List, Optional, Literal, Union, TypedDict

# Define action types
ActionType = Literal['PhoneTransfer', 'QueueTransfer', 'FlowTransfer', 'Prompt']

class BaseAction(TypedDict, total=False):
    """Base action for menu items"""
    type: ActionType

    # Optional fields
    customHandler: Optional[str]  # Lambda ARN if provided

class TransferAction(BaseAction, total=False):
    """Base transfer action with optional prompts"""
    preTransferPrompt: Optional[str]  # Prompt played before transfer
    openCheckKey: Optional[str]  # OMP integration key
    voicemailKey: Optional[str]  # Voicemail key if call not answered

class PhoneTransferAction(TransferAction):
    """Transfer to a phone number"""
    type: Literal['PhoneTransfer']
    phoneNumber: str  # E.164 format phone number

class QueueTransferAction(TransferAction):
    """Transfer to a standard or agent queue"""
    type: Literal['QueueTransfer']
    queueArn: str  # Amazon Connect Queue ARN

class FlowTransferAction(TransferAction):
    """Transfer to a contact flow"""
    type: Literal['FlowTransfer']
    contactFlowArn: str  # Amazon Connect Contact Flow ARN

class PromptAction(BaseAction, total=False):
    """Play a prompt to the user"""
    type: Literal['Prompt']
    prompt: str
    hangUp: Optional[bool]  # If true, hang up after the prompt

# Union type for all possible actions
MenuAction = Union[PhoneTransferAction, QueueTransferAction, FlowTransferAction, PromptAction]

class MenuItem(TypedDict, total=False):
    """Defines an IVR menu item (Associated with a lex intent)"""
    utterances: List[str]  # Phrases associated with this menu item
    confirmation: Optional[str]  # Prompt to confirm the intent if provided
    action: MenuAction  # Action to take when selected

class RequiredIntent(TypedDict):
    """Basic intent with utterances and a response"""
    utterances: List[str]
    response: str

class MenuLocale(TypedDict):
    """Locale configuration for the menu bot"""
    locale_id: str
    voice_id: str
    greeting: str  # Initial IVR greeting
    more_prompt: str  # Prompt to ask if caller needs more help
    help: RequiredIntent  # Help intent
    hang_up: RequiredIntent  # Hang up intent (e.g., "no" to more_prompt)
    menu: Dict[str, MenuItem]  # Menu items defining bot intents and actions

class MenuBot(TypedDict):
    """Top-level menu bot configuration"""
    name: str
    description: str
    locales: List[MenuLocale]