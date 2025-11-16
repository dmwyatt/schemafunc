import click
import re
import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status

console = Console()


def run_command(command, description):
    with console.status(f"[bold green]{description}...", spinner="dots"):
        result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        console.print(f"[bold red]Error:[/bold red] {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def check_uncommitted_changes():
    result = run_command(["git", "status", "--porcelain"],
                         "Checking for uncommitted changes")
    if result:
        lines = result.strip().splitlines()
        if len(lines) == 1 and lines[0].endswith("dev_scripts/release.py"):
            # ignore changes to this script. Makes testing easier.
            return

        console.print("[bold red]Error:[/bold red] There are uncommitted changes.")
        sys.exit(1)


def check_main_branch():
    result = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "Checking current branch",
    )
    if result != "main":
        console.print("[bold red]Error:[/bold red] Not on the main branch.")
        sys.exit(1)


def get_current_version():
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', content)
    if not match:
        console.print(
            "[bold red]Error:[/bold red] Could not find version in pyproject.toml."
        )
        sys.exit(1)

    return match.group(1)


def calculate_new_version(current_version, version=None):
    if version:
        return version
    major, minor, patch = map(int, current_version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def bump_version(version):
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        content = f.read()

    new_content, count = re.subn(
        r'(?m)^(version\s*=\s*")[^"]+(")',
        rf'\1{version}\2',
        content,
        count=1,
    )

    if count == 0:
        console.print(
            "[bold red]Error:[/bold red] Could not update version in pyproject.toml."
        )
        sys.exit(1)

    with open("pyproject.toml", "w", encoding="utf-8") as f:
        f.write(new_content)


def commit_and_tag(version):
    version_tag = f"v{version}"
    run_command(["git", "add", "pyproject.toml"], "Staging changes")
    run_command(["git", "commit", "-m", f"Bump version to {version}"],
                "Committing changes")
    run_command(["git", "tag", "-a", version_tag, "-m", f"Release {version_tag}"],
                "Creating tag")
    run_command(["git", "push", "origin", "main"], "Pushing to main branch")
    run_command(["git", "push", "origin", version_tag], "Pushing new tag")


def preview_changes(current_version, new_version):
    table = Table(title="Proposed Changes")
    table.add_column("Action", style="cyan")
    table.add_column("Detail", style="green")

    table.add_row("Current Version", current_version)
    table.add_row("New Version", new_version)
    table.add_row("Commit Message", f"Bump version to {new_version}")
    table.add_row("New Tag", f"v{new_version}")
    table.add_row("Push Changes", "To 'main' branch")
    table.add_row("Push Tag", f"v{new_version}")

    console.print(Panel(table, expand=False))


@click.command()
@click.option('--version',
              help='Specific version to set. If not provided, patch version will be bumped.')
def main(version):
    """Bump version, commit changes, and create a new release tag."""
    check_uncommitted_changes()
    check_main_branch()

    current_version = get_current_version()
    new_version = calculate_new_version(current_version, version)

    preview_changes(current_version, new_version)

    if click.confirm("Do you want to proceed with these changes?"):
        bump_version(new_version)
        commit_and_tag(new_version)
        console.print(
            f"[bold green]Successfully released version {new_version}[/bold green]")
    else:
        console.print("[yellow]Operation cancelled.[/yellow]")


if __name__ == "__main__":
    main()
