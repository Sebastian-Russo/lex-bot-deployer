from constructs import Construct
from ..constructs.simple_bot import SimpleBot
from aws_cdk import aws_iam as iam
from typing import Optional

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
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        # Create locales with Agent/Callback/Voicemail intents
        locales = [
            {
                "locale_id": "en_US",
                "voice_id": "Joanna",
                "intents": [
                    {
                        "name": "Agent",
                        "utterances": [
                            'agent', 'representative', 'can I speak to an agent?',
                            'help', 'can I talk to someone?'
                        ],
                    },
                    {
                        "name": "Callback",
                        "utterances": [
                            'request a callback', 'callback', 'I would like a call back',
                            'Could you call me back?'
                        ],
                    },
                    {
                        "name": "Voicemail",
                        "utterances": [
                            'leave a voicemail', 'voicemail', 'leave a message',
                            'message', 'I would like to leave a message'
                        ],
                    },
                    # Required fallback intent
                    {
                        "name": "FallbackIntent",
                        "description": "Default intent when no other intent matches",
                        "parentIntentSignature": "AMAZON.FallbackIntent",
                        "utterances": []
                    }
                ]
            },
            {
                "locale_id": "es_US",
                "voice_id": "Lupe",
                "intents": [
                    {
                        "name": "Agent",
                        "utterances": [
                            'agente', 'representante', 'puedo hablar con un agente?',
                            'ayuda', 'puedo hablar con alguien?'
                        ],
                    },
                    {
                        "name": "Callback",
                        "utterances": [
                            'solicitar una devolucion de llamada', 'llamar de vuelta',
                            'me gustaria que me devolvieran la llamada',
                            'podrias devolverme la llamada?'
                        ],
                    },
                    {
                        "name": "Voicemail",
                        "utterances": [
                            'dejar un mensaje de voz', 'mensaje de voz',
                            'deja un mensaje', 'mensaje',
                            'me gustaria dejar un mensaje'
                        ],
                    },
                    # Required fallback intent
                    {
                        "name": "FallbackIntent",
                        "description": "Intent por defecto cuando ningún otro intent coincide",
                        "parentIntentSignature": "AMAZON.FallbackIntent",
                        "utterances": []
                    }
                ]
            }
        ]

        # Ensure we have valid default values
        if idle_session_ttl_in_seconds is None:
            idle_session_ttl_in_seconds = 300  # Default to 5 minutes
        if nlu_confidence_threshold is None:
            nlu_confidence_threshold = 0.75  # Default to 75%

        super().__init__(
            scope, id,
            name=f"{prefix}-agent-busy",
            description=description,
            locales=locales,
            role=role,
            idle_session_ttl_in_seconds=idle_session_ttl_in_seconds,
            nlu_confidence_threshold=nlu_confidence_threshold,
            log_group=log_group,
            audio_bucket=audio_bucket,
            connect_instance_arn=connect_instance_arn,
            **kwargs
        )