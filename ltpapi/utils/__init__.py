import click
from flask import Flask

@click.command()
def initdb():
    click.echo('Init DB')
    import pdb; pdb.set_trace()

