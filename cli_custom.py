"""Sample CLI with custom click command"""

from textwrap import dedent

import click


class CustomCliCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional help info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write("\n\n")
        formatter.write(
            dedent(
                f"""
CLI Overview

This is a sample CLI with custom help text.

This help text will appear after the command description.
"""
            )
        )
        help_text += formatter.getvalue()
        return help_text


@click.command(cls=CustomCliCommand, name="cli")
@click.option("--name", default="World", help="Name to greet")
def cli(name):
    """Sample CLI with custom click command"""
    click.echo(f"Hello, {name}!")


if __name__ == "__main__":
    cli()
