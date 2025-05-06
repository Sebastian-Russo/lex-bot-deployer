from aws_cdk import Aws
from aws_cdk import aws_iam as iam
from aws_cdk import custom_resources as cr
from constructs import Construct
from dataclasses import dataclass
from typing import Optional

@dataclass
class UpdateNeuralEngineProps:
    """Properties for updating a Lex bot locale to use neural engine"""
    bot_id: str
    locale_id: str
    nlu_intent_confidence_threshold: float
    voice_id: str
    description: Optional[str] = None

class UpdateNeuralEngine(cr.AwsCustomResource):
    """
    CfnBot does not support engine updates, so making the change via custom resource
    TODO: This construct was originally written in 2023-Q4, this setting may now be implemented
    """
    def __init__(self, scope: Construct, id: str, props: UpdateNeuralEngineProps):
        bot_id = props.bot_id
        locale_id = props.locale_id
        description = props.description
        nlu_intent_confidence_threshold = props.nlu_intent_confidence_threshold
        voice_id = props.voice_id

        # Define the SDK call
        sdk_call = {
            "service": "LexModelsV2",
            "action": "updateBotLocale",
            "parameters": {
                "botId": bot_id,
                "botVersion": "DRAFT",
                "localeId": locale_id,
                "description": description,
                "nluIntentConfidenceThreshold": nlu_intent_confidence_threshold,
                "voiceSettings": {
                    "voiceId": voice_id,
                    "engine": "neural",
                }
            },
            "physical_resource_id": cr.PhysicalResourceId.of(id),
        }

        # Reset engine when custom resource is deleted
        delete_sdk_call = {
            **sdk_call,
            "parameters": {
                **sdk_call["parameters"],
                "voiceSettings": {
                    **sdk_call["parameters"]["voiceSettings"],
                    "engine": "standard",
                }
            }
        }

        super().__init__(
            scope,
            id,
            install_latest_aws_sdk=False,
            on_create=sdk_call,
            on_update=sdk_call,
            on_delete=delete_sdk_call,
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["lex:UpdateBotLocale"],
                    resources=[
                        # Broader permission to avoid race condition
                        f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:bot/*",
                    ]
                )
            ])
        )