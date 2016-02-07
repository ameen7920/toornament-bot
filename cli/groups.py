import click
import boto3


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
