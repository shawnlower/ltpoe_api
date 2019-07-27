import click
from flask.cli import with_appcontext
from flask import current_app

from . import get_connection


@click.command('load', help='Initialize a new store')
@click.option(
    '-f',
    '--file',
    type=click.File('r'),
    required=True,
)
@with_appcontext
def load(file):
    conn = get_connection(current_app)
    click.echo(f'Loading data from {file}.')
    conn.load(file)


@click.option(
    '-f',
    '--file',
    type=click.File('w'),
    required=True,
)
@click.command(help='Dump store to a file in turtle format')
@with_appcontext
def dump(file):
    conn = get_connection(current_app)
    click.echo(f'Dumping store to {file.name}')
    file.write(conn.dump())


@click.command(
    help='Dump flask config to stdout in newline-separated KEY=VALUE format')
@with_appcontext
def dump_config():
    click.echo('\n'.join([ f'{k}="{v}"' for k,v in current_app.config.items()]))

