from constructs import Construct
from ..constructs.simple_bot import SimpleBot
from aws_cdk import aws_iam as iam
from typing import Optional


class OfficeClosedBot(SimpleBot):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        prefix: str,
        connect_instance_arn: str,
        description: Optional[str] = None,
        role: Optional[iam.IRole] = None,
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs,
    ):
        # Create locales with Emergency and Callback intents

        locales = [
            {
                'locale_id': 'en_US',
                'voice_id': 'Joanna',
                'intents': [
                    {
                        'name': 'Emergency',
                        'utterances': [
                            'emergency',
                            'urgent',
                            'help',
                            'I need help now',
                            'this is an emergency',
                        ],
                    },
                    {
                        'name': 'Callback',
                        'utterances': [
                            'request a callback',
                            'callback',
                            'I would like a call back',
                            'Could you call me back?',
                        ],
                    },
                ],
            },
            {
                'locale_id': 'es_US',
                'voice_id': 'Lupe',
                'intents': [
                    {
                        'name': 'Emergency',
                        'utterances': [
                            'emergencia',
                            'urgente',
                            'ayuda',
                            'necesito ayuda ahora',
                            'esto es una emergencia',
                        ],
                    },
                    {
                        'name': 'Callback',
                        'utterances': [
                            'solicitar una devolucion de llamada',
                            'llamar de vuelta',
                            'me gustaria que me devolvieran la llamada',
                            'podrias devolverme la llamada?',
                        ],
                    },
                ],
            },
        ]

        # Ensure we have valid default values
        if idle_session_ttl_in_seconds is None:
            idle_session_ttl_in_seconds = 300  # Default to 5 minutes
        if nlu_confidence_threshold is None:
            nlu_confidence_threshold = 0.75  # Default to 75%

        super().__init__(
            scope,
            id,
            name=f'{prefix}-office-closed',
            description=description,
            locales=locales,
            role=role,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            nlu_confidence_threshold=nlu_confidence_threshold,
            log_group=log_group,
            audio_bucket=audio_bucket,
            connect_instance_arn=connect_instance_arn,
            **kwargs,
        )
