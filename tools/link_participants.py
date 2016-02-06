#!/usr/bin/env python
import csv

import boto3
import click

from client import Client


@click.command()
@click.argument('export-csv', type=click.File('rb'), required=False)
@click.option('--api-key', envvar='TOORNAMENT_API_KEY', help=(
    'API key for Toornament API. Create new Application on '
    'https://developer.toornament.com/applications to obtain a key. You can '
    'set default value using TOORNAMENT_API_KEY env variable.'
))
@click.option('--tournament-id', envvar='TOORNAMENT_ID', help=(
    'Your tournament ID. Get it from url while browsing '
    'https://www.toornament.com/admin/tournaments/. You can set default value '
    'using TOORNAMENT_ID env variable.'
))
@click.option('--table', envvar='PARTICIPANTS_TABLE', help=(
    'DynamoDB table to store participant-to-telegram linking. You can set '
    'default value using PARTICIPANTS_TABLE env variable.'

))
def link(export_csv, api_key, tournament_id, table):
    emails = {row['Player/Team name'].decode('utf-8'): row['Player email']
              for row in csv.DictReader(export_csv)} if export_csv else {}

    dynamodb = boto3.resource('dynamodb')
    users = dynamodb.Table(table)

    for p in Client(api_key).list_participants(tournament_id):
        name = p['name']
        users.put_item(Item={
            'participant_id': p['id'],
            'tournament_id': tournament_id,
            'name': name,
            'foo': 2,
        })
        if name not in emails:
            msg = u'Unknown email for {u}'.format(u=name)
            click.echo(click.style(msg, fg='red'), err=True)
        click.echo(u'{u} {i}'.format(u=name, i=p['id']))

if __name__ == '__main__':
    link()
