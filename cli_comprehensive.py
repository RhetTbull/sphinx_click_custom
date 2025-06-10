"""Comprehensive CLI example with custom help and all Click features"""

from textwrap import dedent
import click


class CustomCliCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional help info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(
            dedent(
                f"""
🚀 ADVANCED CLI TOOL

This is a comprehensive example showcasing all Click features with custom help formatting.

{help_text}

📝 ADDITIONAL NOTES:
- Use environment variables to set default values
- Check the examples section for common usage patterns
- All commands support --help for detailed information

For more help, visit: https://example.com/docs
"""
            )
        )
        return formatter.getvalue()


class CustomGroup(click.Group):
    """Custom click.Group that overrides get_help() to show additional help info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()
        formatter.write(
            dedent(
                f"""
🎯 COMMAND GROUP

This group contains multiple related commands.

{help_text}

💡 TIP: Use 'COMMAND --help' to get detailed help for each subcommand.
"""
            )
        )
        return formatter.getvalue()


@click.group(cls=CustomGroup, name="myapp")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
    envvar="MYAPP_CONFIG"
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (use multiple times for more verbose output)"
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format for results"
)
@click.version_option("1.0.0", "--version", "-V", message="MyApp version %(version)s")
@click.pass_context
def cli(ctx, config, verbose, output_format):
    """A comprehensive CLI application demonstrating all Click features.
    
    This application showcases options, arguments, environment variables,
    subcommands, and custom help formatting.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['output_format'] = output_format


@cli.command(cls=CustomCliCommand)
@click.argument("input_file", type=click.File('r'))
@click.argument("output_file", type=click.File('w'), required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "xml"]),
    default="csv",
    help="Input file format",
    show_default=True
)
@click.option(
    "--delimiter",
    "-d",
    default=",",
    help="Field delimiter for CSV files",
    show_default=True
)
@click.option(
    "--skip-header/--no-skip-header",
    default=False,
    help="Skip the first line as header"
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Maximum number of records to process"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually doing it"
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Password for authentication"
)
@click.pass_context
def process(ctx, input_file, output_file, format, delimiter, skip_header, limit, dry_run, password):
    """Process data files with various options and transformations.
    
    This command demonstrates arguments, multiple option types, flags,
    and environment variable integration.
    
    Examples:
        myapp process input.csv output.csv --format csv
        myapp process data.json --format json --limit 100
    """
    verbose = ctx.obj['verbose']
    if verbose:
        click.echo(f"Processing {input_file.name} in {format} format...")
    
    if dry_run:
        click.echo("DRY RUN: Would process the file but not making actual changes")
    
    click.echo(f"Authenticated with password: {'*' * len(password)}")


@cli.group(cls=CustomGroup)
def database():
    """Database management commands.
    
    This subgroup contains commands for managing database operations
    like migrations, backups, and maintenance tasks.
    """
    pass


@database.command(cls=CustomCliCommand)
@click.argument("table_name")
@click.option(
    "--host",
    "-h",
    default="localhost",
    help="Database host",
    envvar="DB_HOST",
    show_default=True
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=5432,
    help="Database port",
    envvar="DB_PORT",
    show_default=True
)
@click.option(
    "--user",
    "-u",
    help="Database username",
    envvar="DB_USER",
    required=True
)
@click.option(
    "--ssl/--no-ssl",
    default=True,
    help="Use SSL connection"
)
@click.option(
    "--timeout",
    type=float,
    default=30.0,
    help="Connection timeout in seconds",
    show_default=True
)
def backup(table_name, host, port, user, ssl, timeout):
    """Backup a specific database table.
    
    This command creates a backup of the specified table with
    configurable connection parameters and SSL options.
    
    The backup file will be saved with timestamp in the filename.
    """
    click.echo(f"Backing up table '{table_name}' from {host}:{port}")
    click.echo(f"User: {user}, SSL: {ssl}, Timeout: {timeout}s")


@database.command(cls=CustomCliCommand)
@click.argument("migration_file", type=click.Path(exists=True))
@click.option(
    "--rollback",
    is_flag=True,
    help="Rollback the migration instead of applying it"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force migration even if there are warnings"
)
def migrate(migration_file, rollback, force):
    """Apply or rollback database migrations.
    
    This command handles database schema changes through migration files.
    Use --rollback to undo a migration, and --force to override warnings.
    """
    action = "Rolling back" if rollback else "Applying"
    click.echo(f"{action} migration: {migration_file}")
    
    if force:
        click.echo("FORCE mode enabled - ignoring warnings")


@cli.command(cls=CustomCliCommand)
@click.argument("targets", nargs=-1, required=True)
@click.option(
    "--concurrency",
    "-j",
    type=int,
    default=1,
    help="Number of parallel jobs",
    show_default=True
)
@click.option(
    "--retry-count",
    type=int,
    default=3,
    help="Number of retry attempts on failure",
    show_default=True
)
@click.option(
    "--include",
    multiple=True,
    help="Include patterns (can be used multiple times)"
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude patterns (can be used multiple times)"
)
def deploy(targets, concurrency, retry_count, include, exclude):
    """Deploy to one or more targets.
    
    This command supports multiple arguments and demonstrates
    various option types including multiple values.
    
    Examples:
        myapp deploy staging production
        myapp deploy prod --include "*.py" --exclude "test_*"
    """
    click.echo(f"Deploying to targets: {', '.join(targets)}")
    click.echo(f"Concurrency: {concurrency}, Retries: {retry_count}")
    
    if include:
        click.echo(f"Include patterns: {', '.join(include)}")
    if exclude:
        click.echo(f"Exclude patterns: {', '.join(exclude)}")


if __name__ == "__main__":
    cli()