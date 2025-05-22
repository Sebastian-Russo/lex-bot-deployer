from typing import List, Optional

from aws_cdk import aws_iam as iam
from constructs import Construct

from ..constructs.simple_bot import (
    SimpleBot,
    SimpleBotProps,
    SimpleIntent,
    SimpleLocale,
)


class AgentBusyBot(SimpleBot):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        # Create locales with Agent/Callback/Voicemail intents
        locales: List[SimpleLocale] = [
            SimpleLocale(
                locale_id='en_US',
                voice_id='Joanna',
                intents=[
                    SimpleIntent(
                        name='Agent',
                        utterances=[
                            'agent',
                            'representative',
                            'can I speak to an agent?',
                            'help',
                            'can I talk to someone?',
                        ],
                    ),
                    SimpleIntent(
                        name='Callback',
                        utterances=[
                            'request a callback',
                            'callback',
                            'I would like a call back',
                            'Could you call me back?',
                        ],
                    ),
                    SimpleIntent(
                        name='Voicemail',
                        utterances=[
                            'leave a voicemail',
                            'voicemail',
                            'leave a message',
                            'message',
                            'I would like to leave a message',
                            'I want to leave a voicemail',
                        ],
                    ),
                ],
            ),
            SimpleLocale(
                locale_id='es_US',
                voice_id='Lupe',
                intents=[
                    SimpleIntent(
                        name='Agent',
                        utterances=[
                            'agente',
                            'representante',
                            'puedo hablar con un agente?',
                            'ayuda',
                            'puedo hablar con alguien?',
                        ],
                    ),
                    SimpleIntent(
                        name='Callback',
                        utterances=[
                            'solicitar una devolucion de llamada',
                            'llamar de vuelta',
                            'me gustaria que me devolvieran la llamada',
                            'podrias devolverme la llamada?',
                        ],
                    ),
                    SimpleIntent(
                        name='Voicemail',
                        utterances=[
                            'dejar un mensaje de voz',
                            'mensaje de voz',
                            'deja un mensaje',
                            'mensaje',
                            'me gustaria dejar un mensaje',
                        ],
                    ),
                ],
            ),
        ]

        super().__init__(
            scope,
            id,
            props=SimpleBotProps(
                name=f'{prefix}-agent-busy',
                description=description,
                locales=locales,
                role=role,
                idle_session_ttl_in_seconds=300,
                nlu_confidence_threshold=0.75,
                log_group=log_group,
                audio_bucket=audio_bucket,
                connect_instance_arn=connect_instance_arn,
            ),
            **kwargs,
        )
