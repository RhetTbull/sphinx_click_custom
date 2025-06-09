"""Sample CLI with custome click command"""

from textwrap import dedent

import click


class CliCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional help info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter(width=80)
        formatter.write("\n\n")
        formatter.write(
            dedent(
                f"""
CLI Overview

This is a sample CLI with a custom click command. To use it, run the following command:

cli --name <name>

{help_text}

"""
            )
        )
        help_text += formatter.getvalue()
        return help_text


@click.command(cls=CliCommand, name="cli")
def cli():
    """Sample CLI with custome click command"""
    click.echo("Hello, World!")


if __name__ == "__main__":
    cli()
