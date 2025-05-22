from typing import Mapping

from aws_cdk import aws_lambda as lambda_
from constructs import Construct


def create_lambda(
    scope: Construct,
    id: str,
    code_path: str,
    function_name: str = None,
    description: str = None,
    environment: Mapping[str, str] = {},
):
    stage = scope.node.try_get_context('stage') or 'dev'

    # Default environment variables with any provided ones merged in
    merged_env = {
        'LOGGING_LEVEL': 'ERROR' if stage == 'prod' else 'DEBUG',
        **environment,
    }

    return lambda_.Function(
        scope,
        id,
        function_name=function_name,
        description=description,
        runtime=lambda_.Runtime.PYTHON_3_9,
        handler='index.handler',
        code=lambda_.Code.from_asset(code_path),
        environment=merged_env,
    )
