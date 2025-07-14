#!/usr/bin/env python3

# pylint: disable=import-error
from aws_cdk import App, Environment

from infrastructure.lex_stack import LexStack

app = App()
prefix = 'lex-bot-deployer'

LexStack(
    app,
    'LexBotDeployer',
    prefix=prefix,
    env=Environment(account='308665918648', region='us-east-1'),
    connect_instance_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea',
    agent_transfer_queue_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/queue/dfce6ff7-c5be-4000-8113-8c4a99c72389',
    city_manager_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/4a209a43-7401-43f0-ab14-adcc6bb8b781',
    reprint_1099_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/a08c07f3-1af8-4306-8ce6-5b5a252e7dc8',
    pamphlet_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/4d3bf4e8-f1ff-4808-9de9-cfd2206984c4',
    medicare_enrollment_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/7136ccab-51a1-438e-921f-49244f341ba6',
    medicare_card_replacement_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/cd58671d-abc3-4625-ba27-b4e98fde2fcf',
    ssn_replacement_form_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/7aff72cf-ba07-43d3-8ee7-8516349847d3',
    change_of_address_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/e66bfb50-d271-49f2-8ba3-474792076aea',
    benefit_payment_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/67b97347-2363-4a26-8e98-a8b40459661a',
    office_locator_flow_arn='arn:aws:connect:us-east-1:308665918648:instance/ee5e36fa-330b-4a91-995d-c218d84b8fea/contact-flow/f378725b-f83d-40c0-95fc-a6aa44940ef9',
)

app.synth()
