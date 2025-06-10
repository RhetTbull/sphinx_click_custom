"""Sample CLI with click command"""

import click


@click.command()
@click.option("--name", default="World", help="Name to greet")
def cli(name):
    """Sample click CLI """
    click.echo(f"Hello, {name}!")


if __name__ == "__main__":
    cli()
