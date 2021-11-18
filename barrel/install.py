# An initial setup script that
# - requires no external dependencies (purely Python 3.X)
# - creates a virtual environment
# - installs the requirements.txt file
# Created by Dave Gaeddert <dave.gaeddert@dropseed.dev>, 2021

import sys
import os
import subprocess
import re
import shutil


class Abort(Exception):
    pass


class Installer:
    VENV_NAME = ".venv"
    REQUIREMENTS_FILE = "requirements.txt"

    def __init__(self, package: str, entrypoint_name: str = "", debug: bool = False):
        self.package_input = package
        self.debug = debug
        self.package_name, self.package_constraint = self.parse_package_input(
            self.package_input
        )
        self.entrypoint_name = entrypoint_name or self.package_name

    def parse_package_input(self, package_input: str):
        package_parts = re.split(r"(?<!\\)[><~^=]", package_input)
        if len(package_parts) == 1:
            package_name = package_parts[0]
            if "/" in package_name:
                # Quick way to account for paths right now...
                package_name = package_name.split("/")[-1]
            package_constraint = None
        else:
            package_name = package_parts[0]
            package_constraint = package_parts[1]
            package_constraint = package_constraint.replace("\\", "")

        return package_name, package_constraint

    def install(self, reinstall: bool = False):
        self.event(f"Installing {self.package_input} into this directory")

        if not self.in_venv() and self.has_existing():
            if reinstall:
                self.remove_existing()
            else:
                self.error(
                    f"Use --reinstall to overwrite the existing {self.VENV_NAME} and {self.REQUIREMENTS_FILE}"
                )
                raise Abort()

        self.create_venv()
        self.pip_install()

        package_installed = self.get_installed_package()

        if not package_installed:
            self.error(f"Could not find a pinned version of {package}")
            raise Abort()

        self.save_requirements(package_installed)
        self.check_path()
        self.check_gitignore()

        self.success(f"\nSuccessfully installed {package_installed}!")

    def in_venv(self):
        return sys.executable.startswith(os.path.abspath(self.VENV_NAME) + os.sep)

    def entrypoint_available(self):
        which = shutil.which(self.entrypoint_name)
        if not which:
            return False
        rel = os.path.relpath(which)
        return rel.startswith(self.VENV_NAME)

    def has_existing(self):
        venv_exists = os.path.exists(self.VENV_NAME)
        requirements_exists = os.path.exists(self.REQUIREMENTS_FILE)

        if venv_exists or requirements_exists:
            if venv_exists and requirements_exists:
                self.warn(
                    f"- Both a virtual environment ({self.VENV_NAME}) and a requirements file ({self.REQUIREMENTS_FILE}) already exist"
                )
            elif venv_exists:
                self.warn(f"- A virtual environment ({self.VENV_NAME}) already exists")
            elif requirements_exists:
                self.warn(
                    f"- A requirements file ({self.REQUIREMENTS_FILE}) already exists"
                )

            return True

    def remove_existing(self):
        venv_exists = os.path.exists(self.VENV_NAME)
        requirements_exists = os.path.exists(self.REQUIREMENTS_FILE)

        if venv_exists:
            self.event(f"  - Removing existing {self.VENV_NAME}")
            shutil.rmtree(self.VENV_NAME)

        if requirements_exists:
            self.event(f"  - Removing existing {self.REQUIREMENTS_FILE}")
            os.remove(self.REQUIREMENTS_FILE)

    def create_venv(self):
        self.event(f"- Creating a virtual environment at {self.VENV_NAME}")
        subprocess.check_call([sys.executable, "-m", "venv", self.VENV_NAME])

    def pip_install(self):
        self.event(f"- Installing {self.package_input} with {self.VENV_NAME}/bin/pip")
        subprocess.check_call(
            [f"{self.VENV_NAME}/bin/pip", "install", self.package_input],
            stdout=sys.stdout if self.debug else subprocess.DEVNULL,
        )

    def save_requirements(self, package_installed: str):
        self.event(f"- Saving {self.REQUIREMENTS_FILE}")
        with open(self.REQUIREMENTS_FILE, "w+") as f:
            f.write(f"# This file is managed automatically by {self.package_name}\n")
            f.write(package_installed + "\n")
            # We're intentionally leaving out ALL of the frozen requirements
            # as part of the point of this is to *simplify* the process
            # (the downside to this is that transitive dependencies can and will change without notice)

    def check_path(self):
        if not self.entrypoint_available():
            self.error(
                f'Could not find {self.package_name} in PATH\n\nAn simple solution is to add this to your .bash_profile/.zshrc:\nexport PATH="./.venv/bin:$PATH"'
            )
            raise Abort()

    def check_gitignore(self):
        if os.path.exists(".git") and not self.gitignore_contains(self.VENV_NAME):
            self.warn(
                f"- You should add {self.VENV_NAME} to your .gitignore so that it is not tracked by git"
            )

    def gitignore_contains(self, text: str):
        if not os.path.exists(".gitignore"):
            return False

        with open(".gitignore") as f:
            for line in f:
                if line.strip().lower() == text.lower():
                    return True

        return False

    def get_installed_package(self):
        for line in (
            subprocess.check_output([f"{self.VENV_NAME}/bin/pip", "freeze"])
            .decode("utf-8")
            .splitlines()
        ):
            if re.match(r"^{}\W+".format(self.package_name), line.lower()):
                return line

    def confirm(self, prompt: str):
        return "y" in input(prompt).lower()

    def event(self, text: str):
        """Print in bold if we're in deubg (so regular output is distinguished)"""
        if self.debug:
            print("\033[1m" + text + "\033[0m")
        else:
            print(text)

    def warn(self, text: str):
        print("\033[33m" + text + "\033[0m")

    def error(self, text: str):
        print("\033[31m" + text + "\033[0m")

    def success(self, text: str):
        print("\033[32m" + text + "\033[0m")


if __name__ == "__main__":
    if not sys.version_info >= (3, 5):
        print("This script requires Python 3.5 or higher")
        sys.exit(1)

    if len(sys.argv) < 2 or not sys.argv[1]:
        print("A package name is required as the argument")
        sys.exit(1)

    if "--reinstall" in sys.argv:
        sys.argv.remove("--reinstall")
        reinstall = True
    else:
        reinstall = False

    if "--debug" in sys.argv:
        sys.argv.remove("--debug")
        debug = True
    else:
        debug = False

    if "--entrypoint" in sys.argv:
        entrypoint_name = sys.argv[sys.argv.index("--entrypoint") + 1]
        sys.argv.remove("--entrypoint")
        sys.argv.remove(entrypoint_name)
    else:
        entrypoint_name = ""

    package = sys.argv[1]

    installer = Installer(package=package, entrypoint_name=entrypoint_name, debug=debug)
    try:
        installer.install(reinstall=reinstall)
    except Abort:
        sys.exit(1)
