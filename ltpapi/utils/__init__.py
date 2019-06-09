import click
from flask import Flask
from flask.cli import with_appcontext, AppGroup

app = Flask(__name__)
store_cli = AppGroup('store')

@store_cli.command(help='Initialize a new store')
@click.option('-f', '--file', type=click.File('r'))
def init(fd):
    click.echo(f'Initializing store from {fd}')

@store_cli.command(help='Dump store to stdout in turtle format')
def dump():
    click.echo(f'Dumping store.')

@store_cli.command(
    help='Dump flask config to stdout in newline-separated KEY=VALUE format')
@with_appcontext
def dump_config():
    click.echo('\n'.join([ f'{k}="{v}"' for k,v in app.config.items()]))

app.cli.add_command(store_cli)
