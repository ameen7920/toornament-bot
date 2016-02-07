from __future__ import print_function, unicode_literals

import boto3
import re
from boto3.dynamodb.conditions import Key

from .constants import *  # noqa
from .telegram import send_message
from .toornament import Client


def lambda_handler(event, context):
    tid = event['tournament_id']
    table = boto3.resource('dynamodb').Table('players')

    message = event.get('message', {})
    text = message.get('text', '').strip()
    chat_id = int(message['chat']['id'])

    start = re.match(r'^/start( \w+)?$', text)
    if start:
        code = (start.group(1) or '').strip()
        t = 'Well met!'
        if code:
            response = table.query(
                IndexName='confirmation',
                Select='ALL_PROJECTED_ATTRIBUTES',
                KeyConditionExpression=Key('confirmation_code').eq(code)
            )
            count = response['Count']
            if count > 1:
                t = 'Shit happend! Confirmation code is not unique!'
            elif count == 0:
                t = 'Invalid confirmation code ' + code
            else:
                i = response['Items'][0]
                table.update_item(
                    Key={'participant_id': i['participant_id']},
                    UpdateExpression='SET chat_id = :chat_id',
                    ExpressionAttributeValues={':chat_id': chat_id}
                )
                t = 'Graz! You\'re in!'
    elif text.startswith('/widget'):
        t = 'https://widget.toornament.com/tournaments/{id}/'.format(id=tid)
    elif text.startswith('/matches'):
        t = '\n'.join([m for m in get_matches(event['api_key'], table)])

    if t:
        send_message(event['bot_token'], chat_id, t)
    return {'ok': True}


def get_matches(chat_id, api_key, table):
    response = table.query(
        IndexName=IDX_CHAT,
        Select='ALL_PROJECTED_ATTRIBUTES',
        KeyConditionExpression=Key(ATTR_CHAT).eq(int(chat_id))
    )
    client = Client(api_key)
    for item in response['Items']:
        for m in client.list_matches(item['tournament_id'], item['participant_id']):
            yield m
