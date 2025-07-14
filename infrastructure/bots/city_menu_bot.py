from typing import List, Optional

from constructs import Construct

from ..bots.utterances.help_utterances import HELP_UTTERANCES
from ..constructs.menu_bot.menu_bot import MenuBot, MenuBotProps, MenuLocale
from ..constructs.menu_bot.models import (
    FlowTransferAction,
    MenuItem,
    PhoneTransferAction,
    PromptAction,
    QueueTransferAction,
    RequiredIntent,
)

# Saul Goodman Hotline
TEST_NUMBER = '+16462259369'


class CityMenuBot(Construct):
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
        agent_transfer_queue_arn: str,
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
                greeting='Thank you for calling the city menu sample. How may I help you?',
                more_prompt='Is there anything else I can help you with?',
                help=RequiredIntent(
                    utterances=HELP_UTTERANCES,
                    response='You can say things like, "I would like to speak to someone at City Hall", "I would like to speak to the city manager", or "I have a problem with my bill".',
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
                    'CITY_HALL': MenuItem(
                        utterances=[
                            'I would like to speak to someone at City Hall.',
                            'Connect me to the office of the mayor',
                            'City Commissioners office',
                        ],
                        confirmation='It sounds like you need to speak to city hall, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=agent_transfer_queue_arn,
                        ),
                    ),
                    'CITY_MANAGER': MenuItem(
                        utterances=[
                            'I would like to speak to the city manager.',
                            'Connect me to the city managers office',
                        ],
                        confirmation='I think you need the city manager, is that correct?',
                        action=FlowTransferAction(
                            type='FlowTransfer',
                            contact_flow_arn=city_manager_flow_arn,
                            pre_transfer_prompt='Ok, but instead I will transfer you to the demo flow.',
                        ),
                    ),
                    'PUBLIC_DEFENDER': MenuItem(
                        utterances=[
                            'I need a public defender.',
                            'I got busted',
                            'I dont want to go to jail',
                            'I told the police officer that stuff was not mine!',
                        ],
                        confirmation='I heard you need a public defender, is that correct?',
                        action=PhoneTransferAction(
                            type='PhoneTransfer',
                            phone_number=TEST_NUMBER,
                            pre_transfer_prompt='Ok, I am connecting you to Saul Goodman and Associates.',
                        ),
                    ),
                    'ACCOUNTING': MenuItem(
                        utterances=[
                            'I have a problem with my bill.',
                            'Connect me to accounting',
                            'I want to talk to Bob in accounting',
                            'I want to talk to Bob',
                        ],
                        confirmation='I heard you need Bob in accounting, is that correct?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, I am connecting you to Bob.',
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
            ),
            MenuLocale(
                locale_id='es_US',
                voice_id='Lupe',
                greeting='Gracias por llamar al menú de la ciudad. ¿Cómo puedo ayudarte?',
                more_prompt='¿Hay algo más en lo que pueda ayudarte?',
                help=RequiredIntent(
                    utterances=HELP_UTTERANCES,
                    response='Puedes decir cosas como, "Me gustaría hablar con alguien en el ayuntamiento", "Me gustaría hablar con el alcalde", o "Tengo un problema con mi factura".',
                ),
                hang_up=RequiredIntent(
                    utterances=[
                        'No',
                        'No necesito nada más',
                        'He terminado',
                        'Adiós',
                    ],
                    response='De acuerdo, gracias por llamar y que tengas un buen día!',
                ),
                menu={
                    'CITY_HALL': MenuItem(
                        utterances=[
                            'Me gustaría hablar con alguien en el ayuntamiento.',
                            'Conéctame con el ayuntamiento',
                            'Oficina de los comisionados de la ciudad',
                        ],
                        confirmation='¿Entiendo que necesitas hablar con el ayuntamiento, ¿es correcto?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=agent_transfer_queue_arn,
                        ),
                    ),
                    'CITY_MANAGER': MenuItem(
                        utterances=[
                            'Me gustaría hablar con el alcalde.',
                            'Conéctame con la oficina del alcalde',
                        ],
                        confirmation='¿Entiendo que necesitas hablar con el alcalde, ¿es correcto?',
                        action=FlowTransferAction(
                            type='FlowTransfer',
                            contact_flow_arn=city_manager_flow_arn,
                            pre_transfer_prompt='Ok, pero en su lugar te transferiré al flujo de demostración.',
                        ),
                    ),
                    'PUBLIC_DEFENDER': MenuItem(
                        utterances=[
                            'Necesito un defensor público.',
                            'Me detuvieron',
                            'No quiero ir a la cárcel',
                            'Le dije al policía que eso no era mío!',
                        ],
                        confirmation='¿Entiendo que necesitas un defensor público, ¿es correcto?',
                        action=PhoneTransferAction(
                            type='PhoneTransfer',
                            phone_number=TEST_NUMBER,
                            pre_transfer_prompt='Ok, te estoy conectando con Saul Goodman y Asociados.',
                        ),
                    ),
                    'ACCOUNTING': MenuItem(
                        utterances=[
                            'Tengo un problema con mi factura.',
                            'Conéctame con contabilidad',
                            'Quiero hablar con Bob en contabilidad',
                            'Quiero hablar con Bob',
                        ],
                        confirmation='¿Entiendo que necesitas hablar con Bob en contabilidad, ¿es correcto?',
                        action=QueueTransferAction(
                            type='QueueTransfer',
                            queue_arn=f'{connect_instance_arn}/queue/bob@example.com',
                            pre_transfer_prompt='Ok, te estoy conectando con Bob.',
                        ),
                    ),
                    'MISC': MenuItem(
                        utterances=[
                            '¿Qué tiempo hace?',
                            '¿Puedes ponerme música?',
                            'Juguemos un juego',
                            'Cuéntame un chiste',
                        ],
                        action=PromptAction(
                            type='Prompt',
                            prompt='No soy Alexa, por favor no me hagas preguntas frívolas. Adiós.',
                            hang_up=True,
                        ),
                    ),
                },
            ),
        ]

        # Create the menu bot
        MenuBot(
            self,
            'City',
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
