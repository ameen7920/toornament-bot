#!/usr/bin/env python
import click

from app import function
from cli.groups import cli


@cli.command()
@click.argument('chat-id')
@click.pass_obj
def matches(obj, chat_id):
    res = function.get_matches(chat_id, obj['api_key'], obj['table'])
    for m in res:
        click.echo(m)


@cli.command()
@click.argument('chat-id')
@click.argument('confirmation-code')
@click.pass_obj
def start(obj, chat_id, confirmation_code):
    res = function.start(chat_id, confirmation_code, obj['table'])
    click.echo(res)


if __name__ == '__main__':
    cli(obj={})
