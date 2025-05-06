from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from constructs import Construct
from dataclasses import dataclass
from typing import Optional

@dataclass
class LexRoleProps:
    role_name: Optional[str] = None
    lex_log_group_name: Optional[str] = None

class LexRole(iam.Role):
    """
    Standard lex role configuration
    """
    def __init__(self, scope: Construct, id: str, props: Optional[LexRoleProps] = None):
        props = props or LexRoleProps()

        super().__init__(
            scope,
            id,
            role_name=props.role_name,
            assumed_by=iam.ServicePrincipal('lexv2.amazonaws.com')
        )

        account = Stack.of(self).account
        region = Stack.of(self).region

        # Use default log group name if not provided
        lex_log_group_name = props.lex_log_group_name or '*'

        # Create and attach policy
        policy = iam.Policy(
            self,
            'LexPolicy',
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['polly:SynthesizeSpeech'],
                    resources=['*']
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['logs:CreateLogStream', 'logs:PutLogEvents'],
                    resources=[f"arn:aws:logs:{region}:{account}:log-group:{lex_log_group_name}:log-stream:*"]
                ),
                # Uncomment this if using Sentiment Analysis
                # iam.PolicyStatement(
                #     effect=iam.Effect.ALLOW,
                #     actions=['comprehend:DetectSentiment'],
                #     resources=['*']
                # )
            ]
        )

        self.attach_inline_policy(policy)