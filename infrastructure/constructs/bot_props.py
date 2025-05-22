from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotProps:
    """Properties for creating a Lex bot"""

    prefix: str
    connect_instance_arn: str
    description: Optional[str] = None
    role: Optional[iam.IRole] = None
    log_group: Optional[logs.ILogGroup] = None
    audio_bucket: Optional[s3.IBucket] = None
    nlu_confidence_threshold: Optional[float] = None
    idle_session_ttl_in_seconds: Optional[int] = None
    include_sample_flow: Optional[bool] = None
    city_hall_queue_arn: Optional[str] = None
    city_manager_flow_arn: Optional[str] = None
    idle_session_ttl_in_seconds: Optional[int] = None
