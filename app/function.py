from boto3.dynamodb.conditions import Key
from .toornament import Client
from .constants import *  # noqa


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
