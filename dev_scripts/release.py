import subprocess
import sys


def check_uncommitted_changes():
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    if result.stdout:
        print("Error: There are uncommitted changes.")
        sys.exit(1)


def check_main_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
    )
    if result.stdout.strip() != "main":
        print("Error: Not on the main branch.")
        sys.exit(1)


def bump_version(version=None):
    if version:
        subprocess.run(["poetry", "version", version])
    else:
        # Get current version
        result = subprocess.run(["poetry", "version"], capture_output=True, text=True)
        current_version = result.stdout.strip().split()[-1]
        major, minor, patch = map(int, current_version.split("."))
        new_version = f"{major}.{minor}.{patch + 1}"
        subprocess.run(["poetry", "version", new_version])
        version = new_version
    return version


def commit_and_tag(version):
    version_tag = f"v{version}"
    subprocess.run(["git", "add", "pyproject.toml"])
    subprocess.run(["git", "commit", "-m", f"Bump version to {version}"])
    subprocess.run(["git", "tag", "-a", version_tag, "-m", f"Release {version_tag}"])
    subprocess.run(["git", "push", "origin", "main"])
    subprocess.run(["git", "push", "origin", version_tag])


def main(version=None):
    check_uncommitted_changes()
    check_main_branch()
    new_version = bump_version(version)
    commit_and_tag(new_version)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
