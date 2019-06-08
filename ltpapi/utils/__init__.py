import click
from flask import Flask
from flask.cli import with_appcontext, FlaskGroup

@click.group(cls=FlaskGroup, help='Store sub-commands')
def cli_store():
    """Store subcommands"""

@cli_store.command(help='Initialize a new store')
@click.option('-f', '--file', type=click.File('r'))
def init(fd):
    click.echo(f'Initializing store from {fd}')

@cli_store.command(help='Dump store to stdout in turtle format')
def dump():
    click.echo(f'Dumping store.')

@cli_store.command(
    help='Dump flask config to stdout in newline-separated KEY=VALUE format')
@with_appcontext
def dump_config():
    app = Flask(__name__)
    click.echo('\n'.join([ f'{k}="{v}"' for k,v in app.config.items()]))

