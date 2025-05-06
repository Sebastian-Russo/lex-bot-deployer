#!/usr/bin/env python3

import os
from aws_cdk import App, Environment
from lib.lex_stack import LexStack  # This will be the Python version of your LexStack

app = App()
prefix = 'lex-deploy-demo'

LexStack(app, 'Lex',
    stack_name=prefix,
    prefix=prefix,
    env=Environment(
        account='308665918648',
        region='us-east-1'
    ),
    connect_instance_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea',
    city_hall_queue_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/queue/dfce6ff7-c5be-4000-8113-8c4a99c72389',
    city_manager_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/4a209a43-7401-43f0-ab14-adcc6bb8b781'
)

app.synth()
