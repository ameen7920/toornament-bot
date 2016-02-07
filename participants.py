#!/usr/bin/env python
import csv
import hashlib
import hmac

import boto3
import click
from botocore.exceptions import ClientError

from app.constants import *  # noqa
from app.toornament import Client
from app.function import get_matches


@click.group()
@click.option('--table', envvar='PARTICIPANTS_TABLE', help=(
    'DynamoDB table to store participant-to-telegram linking. You can set '
    'default value using PARTICIPANTS_TABLE env variable.'
))
@click.option('--api-key', envvar='TOORNAMENT_API_KEY', help=(
    'API key for Toornament API. Create new Application on '
    'https://developer.toornament.com/applications to obtain a key. You can '
    'set default value using TOORNAMENT_API_KEY env variable.'
))
@click.pass_context
def cli(ctx, table, api_key):
    ctx.obj['table'] = boto3.resource('dynamodb').Table(table)
    ctx.obj['api_key'] = api_key


@cli.command()
@click.argument('export-csv', type=click.File('rb'), required=False)
@click.option('--bot-name', envvar='TELEGRAM_BOT_NAME', help=(
    'Telegram Bot name. More about bots here https://core.telegram.org/bots. '
    'You can set default value using TELEGRAM_BOT_NAME env variable.'
))
@click.option('--tournament-id', envvar='TOORNAMENT_ID', help=(
    'Your tournament ID. Get it from url while browsing '
    'https://www.toornament.com/admin/tournaments/. You can set default value '
    'using TOORNAMENT_ID env variable.'
))
@click.option('--secret', envvar='SECRET_KEY', prompt=True, hide_input=True, help=(
    'Secret key to use as salt for confirmation code. You can set default '
    'value using SECRET_KEY env variable.'
))
@click.pass_obj
def link(ctx_obj, export_csv, bot_name, tournament_id, secret):
    emails = {row['Player/Team name'].decode('utf-8'): row['Player email']
              for row in csv.DictReader(export_csv)} if export_csv else {}

    for p in Client(api_key).list_participants(tournament_id):
        digest = hmac.new(key=str(secret), digestmod=hashlib.sha256)
        digest.update(api_key)
        digest.update(p['id'])
        code = digest.hexdigest()[:32]

        name = p['name']
        ctx_obj['table'].put_item(Item={
            ATTR_PARTICIPANT: p['id'],
            ATTR_TOURNAMENT: tournament_id,
            'name': name,
            ATTR_CODE: code,
        })
        if name not in emails:
            msg = u'Unknown email for {u} share following link manually with this user'.format(u=name)
            click.echo(click.style(msg, fg='red'), err=True)
        else:
            # TODO send email
            pass
        click.echo(u'{u}: {link}'.format(u=name, link=start_url(bot_name, code)))


def start_url(bot, code):
    return 'https://telegram.me/{bot}?start={code}'.format(bot=bot, code=code)


@cli.command()
@click.pass_obj
def setup(ctx_obj):
    table = ctx_obj['table']
    try:
        status = table.table_status
        click.echo('Table {t} is {s}'.format(t=table.name, s=status))
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
        table = boto3.resource('dynamodb').create_table(
            TableName=table.name,
            AttributeDefinitions=[
                {
                    'AttributeName': ATTR_PARTICIPANT,
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': ATTR_TOURNAMENT,
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': ATTR_CHAT,
                    'AttributeType': 'N',
                },
                {
                    'AttributeName': ATTR_CODE,
                    'AttributeType': 'S',
                },
            ],
            KeySchema=[
                {
                    'AttributeName': ATTR_PARTICIPANT,
                    'KeyType': 'HASH',
                },
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': IDX_CHAT,
                    'KeySchema': [
                        {
                            'AttributeName': ATTR_CHAT,
                            'KeyType': 'HASH',
                        },
                        {
                            'AttributeName': ATTR_TOURNAMENT,
                            'KeyType': 'RANGE',
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': [
                            ATTR_PARTICIPANT, ATTR_TOURNAMENT,
                        ],
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1,
                    },
                },
                {
                    'IndexName': IDX_CODE,
                    'KeySchema': [
                        {
                            'AttributeName': ATTR_CODE,
                            'KeyType': 'HASH',
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': [
                            ATTR_PARTICIPANT, ATTR_TOURNAMENT,
                        ],
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1,
                    },
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1,
            },
        )
        table.meta.client.get_waiter('table_exists').wait(TableName=table.name)
        click.echo('Table {t} {s}'.format(t=table.name, s=table.table_status))


@cli.command()
@click.argument('chat-id')
@click.pass_obj
def matches(obj, chat_id):
    res = get_matches(chat_id, obj['api_key'], obj['table'])
    for m in res:
        click.echo(m)

if __name__ == '__main__':
    cli(obj={})
