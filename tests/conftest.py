"""Pytest configuration and fixtures for sphinx_click_custom tests."""

import tempfile
from pathlib import Path
from textwrap import dedent

import click
import pytest
from docutils.core import publish_doctree
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace


class CustomCliCommand(click.Command):
    """Test custom command with get_help override."""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(
            dedent(
                f"""
        🚀 CUSTOM HEADER
        
        This is custom help content before standard help.
        
        {help_text}
        
        📝 CUSTOM FOOTER
        
        This is custom help content after standard help.
        """
            )
        )
        return formatter.getvalue()


class CustomGroup(click.Group):
    """Test custom group with get_help override."""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(
            dedent(
                f"""
        🎯 GROUP HEADER
        
        {help_text}
        
        💡 GROUP FOOTER
        """
            )
        )
        return formatter.getvalue()


@click.command(cls=CustomCliCommand)
@click.option("--name", help="Name to greet")
@click.option(
    "--count", type=int, default=1, help="Number of greetings", show_default=True
)
@click.option(
    "--format",
    type=click.Choice(["plain", "fancy"]),
    default="plain",
    help="Output format",
)
@click.option("--required-opt", required=True, help="Required option")
@click.option("--flag/--no-flag", help="Boolean flag option")
@click.argument("input_file", type=click.File("r"))
@click.argument("output_file", type=click.File("w"), required=False)
def sample_custom_command(
    name, count, format, required_opt, flag, input_file, output_file
):
    """Test command with custom help."""
    pass


@click.group(cls=CustomGroup)
@click.option("--verbose", "-v", count=True, help="Increase verbosity")
def sample_custom_group(verbose):
    """Test group with custom help."""
    pass


@sample_custom_group.command(cls=CustomCliCommand)
@click.argument("table_name")
@click.option("--host", default="localhost", envvar="DB_HOST", help="Database host")
@click.option("--port", type=int, default=5432, envvar="DB_PORT", help="Database port")
def backup(table_name, host, port):
    """Backup a database table."""
    pass


@click.command()
@click.option("--name", help="Name to greet")
def standard_command(name):
    """Standard command without custom help."""
    pass


@pytest.fixture
def temp_sphinx_project():
    """Create a temporary Sphinx project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        srcdir = Path(tmpdir) / "source"
        outdir = Path(tmpdir) / "build"
        doctreedir = Path(tmpdir) / "doctrees"
        confdir = srcdir

        srcdir.mkdir()

        # Create minimal conf.py
        conf_content = dedent(
            """
        extensions = ['sphinx_click_custom.ext']
        """
        )
        (srcdir / "conf.py").write_text(conf_content)

        # Create index.rst
        index_content = dedent(
            """
        Test Documentation
        ==================
        
        .. click-custom:: tests.conftest:sample_custom_command
           :prog: test-custom
        """
        )
        (srcdir / "index.rst").write_text(index_content)

        yield {
            "srcdir": str(srcdir),
            "outdir": str(outdir),
            "doctreedir": str(doctreedir),
            "confdir": str(confdir),
        }


@pytest.fixture
def sphinx_app(temp_sphinx_project):
    """Create a Sphinx application for testing."""
    with docutils_namespace():
        app = Sphinx(
            srcdir=temp_sphinx_project["srcdir"],
            confdir=temp_sphinx_project["confdir"],
            outdir=temp_sphinx_project["outdir"],
            doctreedir=temp_sphinx_project["doctreedir"],
            buildername="html",
            verbosity=0,
            warning=None,
        )
        yield app


@pytest.fixture
def click_context():
    """Create a Click context for testing."""

    def _create_context(command, prog_name="test"):
        return click.Context(command, info_name=prog_name)

    return _create_context
