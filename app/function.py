from __future__ import print_function, unicode_literals

import boto3
import re
from boto3.dynamodb.conditions import Key

from .constants import *  # noqa
from .telegram import send_message
from .toornament import Client


def lambda_handler(event, context):
    table = boto3.resource('dynamodb').Table('players')

    message = event.get('message', {})
    text = message.get('text', '').strip()
    chat_id = int(message['chat']['id'])

    start = re.match(r'^/start( \w+)?$', text)
    if start:
        code = (start.group(1) or '').strip()
        t = start(code, table) if code else 'Well met!'
    elif text.startswith('/widget'):
        t = get_widgets(chat_id, table)
    elif text.startswith('/matches'):
        t = get_matches(chat_id, event['api_key'], table)

    if t:
        send_message(event['bot_token'], chat_id, t)
    return {'ok': True}


def start(chat_id, code, table):
    response = table.query(
        IndexName=IDX_CODE,
        Select='ALL_PROJECTED_ATTRIBUTES',
        KeyConditionExpression=Key(ATTR_CODE).eq(code)
    )
    count = response['Count']
    if count > 1:
        return 'Shit happend! Confirmation code is not unique!'
    elif count == 0:
        return 'Invalid confirmation code ' + code
    else:
        i = response['Items'][0]
        table.update_item(
            Key={ATTR_PARTICIPANT: i[ATTR_PARTICIPANT]},
            UpdateExpression='SET {k} = :chat_id'.format(k=ATTR_CHAT),
            ExpressionAttributeValues={':chat_id': chat_id}
        )
        return 'Graz! You\'re in!'


def tournaments(chat_id, table):
    response = table.query(
        IndexName=IDX_CHAT,
        Select='ALL_PROJECTED_ATTRIBUTES',
        KeyConditionExpression=Key(ATTR_CHAT).eq(int(chat_id))
    )
    for item in response['Items']:
        yield item


def get_widgets(chat_id, table):
    for item in tournaments(chat_id, table):
        yield 'https://widget.toornament.com/tournaments/{id}/'.format(
            id=item[ATTR_TOURNAMENT])


def get_matches(chat_id, api_key, table):
    client = Client(api_key)
    for item in tournaments(chat_id, table):
        for m in client.list_matches(item['tournament_id'], item[ATTR_TOURNAMENT]):
            yield m
