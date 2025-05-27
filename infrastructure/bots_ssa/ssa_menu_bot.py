from typing import List, Optional

from constructs import Construct

from ..constructs.menu_bot.menu_bot import MenuBot, MenuBotProps, MenuLocale
from ..constructs.menu_bot.models import (
    FlowTransferAction,
    MenuItem,
    PromptAction,
    QueueTransferAction,
    RequiredIntent,
)
from .utterances.help_utterances import HELP_UTTERANCES

# Saul Goodman Hotline
TEST_NUMBER = '+16462259369'


class SSAMenuBot(Construct):
    """
    Demonstrates how to implement a lex menu bot which can route to numbers, queues,
    contact flows, and provide information
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        city_hall_queue_arn: str,
        city_manager_flow_arn: str,
        description: Optional[str] = None,
        role=None,
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        locales: List[MenuLocale] = [
            MenuLocale(
                locale_id='en_US',
                voice_id='Joanna',
                greeting='Welcome to the Social Security Administration. Please listen carefully as our menus have recently changed. Para espanol, marque siete.',
                more_prompt='How can I help you today?',
                help=RequiredIntent(
                    utterances=HELP_UTTERANCES,
                    response='You can say things like, "I would like to print a 1099", "I would like a pamphlet", "I want to enroll in medicare","I need to replace my social security card", "I need to change my address", "I want to verify my benefit payments", "I want to change my personal information".',
                ),
                hang_up=RequiredIntent(
                    utterances=[
                        'No',
                        'I dont need anything else',
                        'I am done',
                        'Goodbye',
                    ],
                    response='Ok, thank you for calling, and have a nice day!',
                ),
                menu={
                    '1099_REPRINT': MenuItem(
                        utterances=[
                            'I would like to print a 1099.',
                            'I need to print a 1099.',
                            'I need a 1099.',
                        ],
                        confirmation='It sounds like you need to print a 1099, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=city_hall_queue_arn,
                        ),
                    ),
                    'PAMPHLETS': MenuItem(
                        utterances=[
                            'I would like a pamphlet.',
                            'I need a pamphlet.',
                            'Pamphlet on social security.',
                            'Pamphlet on understanding social security.',
                            'Pamphlet on retirement benefits.',
                            'Pamphlet on disability benefits.',
                            'Pamphlet on survivors benefits.',
                            'Pamphlet on How Work Affects Benefits.',
                            'Pamphlet on Benefits for CHildren with Disabilities.',
                            'Pamphlet on What Every Woman Should Know About Social Security.',
                        ],
                        confirmation='You would like a pamphlet, is that correct?',
                        action=FlowTransferAction(
                            type='FlowTransfer',
                            contact_flow_arn=city_manager_flow_arn,
                            pre_transfer_prompt='Ok, pamphelts. One moment. THere are several pamphlet topics to choose from. I will take you through the list and you can select the ones you want. To skip ahead to the next topic, just say skip topic. To hear it again, say repeat that. And at any time, you can say, I am done. Now, to get started, do you want the pamphlet on Understanding Social Security?',
                        ),
                    ),
                    'MEDICARE_ENROLLMENT': MenuItem(
                        utterances=[
                            'Medicare enrollment.',
                            'I want to enroll in medicare.',
                            'Set up medicare.',
                            'Do I have medicare?',
                        ],
                        confirmation='I heard you want information about medicare, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, medicare. One moment. Are you already enrolled in Medicare?',
                        ),
                    ),
                    'MEDICARE_CARD_REPLACEMENT': MenuItem(
                        utterances=[
                            'Medicare card replacement.',
                            'I want to replace my medicare card.',
                            'I need a new medicare card.',
                            'I need to replace my medicare card.',
                        ],
                        confirmation='I heard you need a new medicare card, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, Medicare Replacement Card. One moment. Did you know you can request a Replacement Medicare Card by going online and using your My S S A account? Go to w w w dot social security dot g o v and select Sign in.',  # prompt P1045, also after is prompt P1173, not included here
                        ),
                    ),
                    'SSN_REPLACEMENT_FORM': MenuItem(
                        utterances=[
                            'SSN replacement form.',
                            'I want to replace my SSN.',
                            'I need a new SSN.',
                            'I need to replace my SSN.',
                        ],
                        confirmation='I heard you need to replace your social security card, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, Social Security Card. One moment. Which of these would you like to do? Get a Replacement Social Social Security Card. Apply for a social security card number. Change personal information. Or go back to the main menu.',  # prompt: P1418
                        ),
                    ),
                    'CHANGE_OF_ADDRESS': MenuItem(
                        utterances=[
                            'Change address.',
                            'I want to change my address.',
                            'I need to change my address.',
                            'I have a different address.',
                        ],
                        confirmation='I heard you need to change your address, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, Change address or phone number. To get started, I have a couple of questions. Are you ceveiving retirement, survivor or disability benefits?',
                        ),
                    ),
                    'BENEFIT_PAYMENT': MenuItem(
                        utterances=[
                            'I want to verify my benefit payments.',
                            'I want to check my benefits.',
                            'Benefits.',
                            'Benefit payment.',
                            'Check benefits.',
                            'Check benefit payments.',
                        ],
                        confirmation='I heard you want to verify your benefit payments, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Alright, benefits verification or proof of income. One moment. You may be able to obtain a benefit verification, sometimes called a proof of income letter, as verification that you do or do not receive benefits by going online and using your My S S A account. Go to w w w dot social security dot g o v and select Sign in.',
                        ),
                    ),
                    'MISC': MenuItem(
                        utterances=[
                            'What is the weather like?',
                            'Can you play me some music?',
                            'Lets play a game',
                            'Tell me a joke',
                        ],
                        action=PromptAction(
                            type='Prompt',
                            prompt='I am not Alexa, Please dont ask me frivolous questions. Goodbye.',
                            hang_up=True,
                        ),
                    ),
                },
            )
        ]

        # Create the menu bot
        MenuBot(
            self,
            'SSAMenuBot',
            props=MenuBotProps(
                prefix=prefix,
                connect_instance_arn=connect_instance_arn,
                description=description,
                role=role,
                idle_session_ttl_in_seconds=300,
                nlu_confidence_threshold=0.75,
                log_group=log_group,
                audio_bucket=audio_bucket,
                include_sample_flow=True,
                locales=locales,
            ),
        )
