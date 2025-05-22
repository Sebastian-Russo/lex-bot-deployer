from constructs import Construct
from aws_cdk import Stack
from ..constructs.menu_bot.menu_bot import MenuBot
from typing import Optional
from ..bots.utterances.help_utterances import HELP_UTTERANCES

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
        city_hall_queue_arn: str,
        city_manager_flow_arn: str,
        description: Optional[str] = None,
        role=None,
        idle_session_ttl_in_seconds: Optional[int] = None,
        nlu_confidence_threshold: Optional[float] = None,
        log_group=None,
        audio_bucket=None,
        **kwargs
    ):
        super().__init__(scope, id)

        # Get current account and region
        stack = Stack.of(self)
        account = stack.account
        region = stack.region

        # Create the menu bot
        MenuBot(
            self, 'City',
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
                    "greeting": "Thank you for calling the city menu sample. How may I help you?",
                    "more_prompt": "Is there anything else I can help you with?",
                    "help": {
                        "utterances": HELP_UTTERANCES,
                        "response": "You can say things like, \"I would like to speak to someone at City Hall\", \"I would like to speak to the city manager\", or \"I have a problem with my bill\".",
                    },
                    "hang_up": {
                        "utterances": ["No", "I dont need anything else", "I am done", "Goodbye"],
                        "response": "Ok, thank you for calling, and have a nice day!",
                    },
                    "menu": {
                        "CITY_HALL": {
                            "utterances": [
                                "I would like to speak to someone at City Hall.",
                                "Connect me to the office of the mayor",
                                "City Commissioners office",
                            ],
                            "confirmation": "It sounds like you need to speak to city hall, is that correct?",
                            "action": {
                                "type": "QueueTransfer",
                                "queueArn": city_hall_queue_arn,
                            },
                        },
                        "CITY_MANAGER": {
                            "utterances": [
                                "I would like to speak to the city manager.",
                                "Connect me to the city managers office"
                            ],
                            "confirmation": "I think you need the city manager, is that correct?",
                            "action": {
                                "type": "FlowTransfer",
                                "contactFlowArn": city_manager_flow_arn,
                                "preTransferPrompt": "Ok, but instead I will transfer you to the demo flow.",
                            },
                        },
                        "PUBLIC_DEFENDER": {
                            "utterances": [
                                "I need a public defender.",
                                "I got busted",
                                "I dont want to go to jail",
                                "I told the police officer that stuff was not mine!",
                            ],
                            "confirmation": "I heard you need a public defender, is that correct?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Ok, I am connecting you to Saul Goodman and Associates.",
                            },
                        },
                        "ACCOUNTING": {
                            "utterances": [
                                "I have a problem with my bill.",
                                "Connect me to accounting",
                                "I want to talk to Bob in accounting",
                                "I want to talk to Bob",
                            ],
                            "confirmation": "I heard you need Bob in accounting, is that correct?",
                            "action": {
                                "type": "QueueTransfer",
                                "queueArn": f"{connect_instance_arn}/queue/bob@example.com",
                                "preTransferPrompt": "Ok, I am connecting you to Bob.",
                            },
                        },
                        "MISC": {
                            "utterances": [
                                "What is the weather like?",
                                "Can you play me some music?",
                                "Lets play a game",
                                "Tell me a joke",
                            ],
                            "action": {
                                "type": "Prompt",
                                "prompt": "I am not Alexa, Please dont ask me frivolous questions. Goodbye.",
                                "hangUp": True,
                            },
                        },
                    },
                    # Convert fallback_intent to menu item for proper inclusion in the intents list
                    "FallbackIntent": {
                        "utterances": [],
                        "action": {
                            "type": "Prompt",
                            "prompt": "I'm not sure I understood what you were asking for. Could you try again?",
                        },
                        "parentIntentSignature": "AMAZON.FallbackIntent"
                    }
                },
                {
                    "locale_id": "es_US",
                    "voice_id": "Lupe",
                    "greeting": "Gracias por llamar al menú de la ciudad. ¿Cómo puedo ayudarte?",
                    "more_prompt": "¿Hay algo más en lo que pueda ayudarte?",
                    "help": {
                        "utterances": HELP_UTTERANCES,
                        "response": "Puedes decir cosas como, \"Me gustaría hablar con alguien en el ayuntamiento\", \"Me gustaría hablar con el alcalde\", o \"Tengo un problema con mi factura\".",
                    },
                    "hang_up": {
                        "utterances": ["No", "No necesito nada más", "He terminado", "Adiós"],
                        "response": "De acuerdo, gracias por llamar y que tengas un buen día!",
                    },
                    "menu": {
                        "CITY_HALL": {
                            "utterances": [
                                "Me gustaría hablar con alguien en el ayuntamiento.",
                                "Conéctame con el ayuntamiento",
                                "Oficina de los comisionados de la ciudad",
                            ],
                            "confirmation": "¿Entiendo que necesitas hablar con el ayuntamiento, ¿es correcto?",
                            "action": {
                                "type": "QueueTransfer",
                                "queueArn": city_hall_queue_arn,
                            },
                        },
                        "CITY_MANAGER": {
                            "utterances": [
                                "Me gustaría hablar con el alcalde.",
                                "Conéctame con la oficina del alcalde"
                            ],
                            "confirmation": "¿Entiendo que necesitas hablar con el alcalde, ¿es correcto?",
                            "action": {
                                "type": "FlowTransfer",
                                "contactFlowArn": city_manager_flow_arn,
                                "preTransferPrompt": "Ok, pero en su lugar te transferiré al flujo de demostración.",
                            },
                        },
                        "PUBLIC_DEFENDER": {
                            "utterances": [
                                "Necesito un defensor público.",
                                "Me detuvieron",
                                "No quiero ir a la cárcel",
                                "Le dije al policía que eso no era mío!",
                            ],
                            "confirmation": "¿Entiendo que necesitas un defensor público, ¿es correcto?",
                            "action": {
                                "type": "PhoneTransfer",
                                "phoneNumber": TEST_NUMBER,
                                "preTransferPrompt": "Ok, te estoy conectando con Saul Goodman y Asociados.",
                            },
                        },
                        "ACCOUNTING": {
                            "utterances": [
                                "Tengo un problema con mi factura.",
                                "Conéctame con contabilidad",
                                "Quiero hablar con Bob en contabilidad",
                                "Quiero hablar con Bob",
                            ],
                            "confirmation": "¿Entiendo que necesitas hablar con Bob en contabilidad, ¿es correcto?",
                            "action": {
                                "type": "QueueTransfer",
                                "queueArn": f"{connect_instance_arn}/queue/bob@example.com",
                                "preTransferPrompt": "Ok, te estoy conectando con Bob.",
                            },
                        },
                        "MISC": {
                            "utterances": [
                                "¿Qué tiempo hace?",
                                "¿Puedes ponerme música?",
                                "Juguemos un juego",
                                "Cuéntame un chiste",
                            ],
                            "action": {
                                "type": "Prompt",
                                "prompt": "No soy Alexa, por favor no me hagas preguntas frívolas. Adiós.",
                                "hangUp": True,
                            },
                        },
                    },
                    "FallbackIntent": {
                        "utterances": [],
                        "action": {
                            "type": "Prompt",
                            "prompt": "No estoy seguro de haber entendido lo que estabas pidiendo. ¿Podrías intentarlo de nuevo?",
                        },
                        "parentIntentSignature": "AMAZON.FallbackIntent"
                    }
                }
            ],
            city_hall_queue_arn=city_hall_queue_arn,
            city_manager_flow_arn=city_manager_flow_arn,
        )