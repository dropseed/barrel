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

    # Installation modes
    MODE_CREATE = "create"
    MODE_INSTALL = "install"
    MODE_UPDATE = "update"
    MODE_REINSTALL = "reinstall"

    def __init__(
        self, package: str, entrypoint_name: str = "", debug: bool = False
    ) -> None:
        self.package_input = package
        self.debug = debug
        self.package_name = self.parse_package_name(self.package_input)
        self.entrypoint_name = entrypoint_name or self.package_name

    def parse_package_name(self, package_input: str) -> str:
        package_name = ""

        package_parts = re.split(r"(?<!\\)[><~^=]", package_input)
        if len(package_parts) == 1:
            package_name = package_parts[0]
            if "/" in package_name:
                # Quick way to account for paths right now...
                package_name = package_name.split("/")[-1]
        else:
            package_name = package_parts[0]

        return package_name

    def get_mode(self, reinstall: bool, update: bool) -> str:
        if self.in_venv():
            # This is the case when running `<package> update`
            # for example, from inside a CLI using Barrel
            return self.MODE_UPDATE

        venv_exists = os.path.exists(self.VENV_NAME)
        requirements_exists = os.path.exists(self.REQUIREMENTS_FILE)

        if not venv_exists and not requirements_exists:
            return self.MODE_CREATE

        if requirements_exists and not venv_exists:
            return self.MODE_INSTALL

        if not requirements_exists and venv_exists:
            self.error(
                f"A {self.VENV_NAME} exists but {self.REQUIREMENTS_FILE} does not... might not be a Barrel-compatible installation?"
            )
            raise Abort()

        if requirements_exists and venv_exists:
            if update:
                return self.MODE_UPDATE
            elif reinstall:
                return self.MODE_REINSTALL
            else:
                self.error(f"Use --reinstall or --update in an existing installation")
                raise Abort()

        return self.MODE_INSTALL

    def run(self, reinstall: bool = False, update: bool = False) -> None:
        mode = self.get_mode(reinstall=reinstall, update=update)

        if mode == self.MODE_CREATE:
            self.install()
        elif mode == self.MODE_INSTALL:
            self.install()
        elif mode == self.MODE_UPDATE:
            self.update()
        elif mode == self.MODE_REINSTALL:
            self.reinstall()

    def create(self) -> None:
        """Creates .venv and requirements.txt"""
        self.preflight(requirements_should_exist=False)
        self.event(f"Setting up {self.package_input} in this directory")

        self.create_venv()
        self.pip_install()

        package_installed = self.get_installed_package()

        if not package_installed:
            self.error(f"Could not find a pinned version of {self.package_name}")
            raise Abort()

        self.save_requirements(package_installed)

        self.check_path()
        self.check_gitignore()

        self.success(f"\nSuccessfully installed {package_installed}!")

    def install(self) -> None:
        """Installs existing requirements.txt"""
        self.preflight(requirements_should_exist=True)
        self.event(f"Installing {self.package_input} into this directory")

        self.create_venv()
        self.pip_install_requirements()

        package_installed = self.get_installed_package()

        self.check_path()
        self.check_gitignore()

        self.success(f"\nSuccessfully installed {package_installed}!")

    def reinstall(self) -> None:
        self.preflight(requirements_should_exist=False)
        self.event(f"Re-installing {self.package_input} into this directory")

        self.remove_existing()
        self.create()

    def update(self) -> None:
        self.preflight(requirements_should_exist=True)
        self.event(f"Updating {self.package_input}")

        if self.package_name == self.package_input:
            # Just update to latest
            self.pip_update()
        else:
            # Could be specifying a version
            self.pip_install()

        package_installed = self.get_installed_package()

        if not package_installed:
            self.error(f"Could not find a pinned version of {self.package_name}")
            raise Abort()

        self.save_requirements(package_installed)

        self.success(f"\nSuccessfully updated {package_installed}!")

    def preflight(self, requirements_should_exist: bool) -> None:
        if os.path.exists("pyproject.toml") or os.path.exists("poetry.lock"):
            print(
                "It looks like you are using Poetry for dependencies. Use the `poetry update` command instead."
            )
            raise Abort()

        if os.path.exists("Pipfile") or os.path.exists("Pipfile.lock"):
            print(
                "It looks like you are using Pipenv for dependencies. Use the `pipenv update` command instead."
            )
            raise Abort()

        if os.path.exists("requirements.in"):
            print(
                "It looks like you are using pip-compile for dependencies. Use the `pip-compile requirements.in` command instead."
            )
            raise Abort()

        if os.path.exists("setup.py"):
            print(
                "It looks like you are using setuptools for dependencies. Use the `python setup.py install` command instead."
            )
            raise Abort()

        if requirements_should_exist and not os.path.exists(
            Installer.REQUIREMENTS_FILE
        ):
            print(
                f"A {self.REQUIREMENTS_FILE} file does not exist, which likely means that you aren't updating a barrel-compatible installation or aren't in the right directory."
            )
            raise Abort()

    def in_venv(self) -> bool:
        return sys.executable.startswith(os.path.abspath(self.VENV_NAME) + os.sep)

    def entrypoint_available(self) -> bool:
        which = shutil.which(self.entrypoint_name)
        if not which:
            return False

        rel = os.path.relpath(which)
        return rel.startswith(self.VENV_NAME)

    def remove_existing(self) -> None:
        venv_exists = os.path.exists(self.VENV_NAME)
        requirements_exists = os.path.exists(self.REQUIREMENTS_FILE)

        if venv_exists:
            self.event(f"  - Removing existing {self.VENV_NAME}")
            shutil.rmtree(self.VENV_NAME)

        if requirements_exists:
            self.event(f"  - Removing existing {self.REQUIREMENTS_FILE}")
            os.remove(self.REQUIREMENTS_FILE)

    def create_venv(self) -> None:
        self.event(f"- Creating a virtual environment at {self.VENV_NAME}")
        subprocess.check_call([sys.executable, "-m", "venv", self.VENV_NAME])

    def pip_install(self) -> None:
        self.event(f"- Installing {self.package_input} with {self.VENV_NAME}/bin/pip")
        subprocess.check_call(
            [f"{self.VENV_NAME}/bin/pip", "install", self.package_input],
            stdout=sys.stdout if self.debug else subprocess.DEVNULL,
        )

    def pip_install_requirements(self) -> None:
        self.event(f"- Installing {self.REQUIREMENTS_FILE}")
        subprocess.check_call(
            [f"{self.VENV_NAME}/bin/pip", "install", "-r", self.REQUIREMENTS_FILE],
            stdout=sys.stdout if self.debug else subprocess.DEVNULL,
        )

    def pip_update(self) -> None:
        self.event(f"- Updating {self.package_input} with {self.VENV_NAME}/bin/pip")
        subprocess.check_call(
            [f"{self.VENV_NAME}/bin/pip", "install", "-U", self.package_input],
            stdout=sys.stdout if self.debug else subprocess.DEVNULL,
        )

    def save_requirements(self, package_installed: str) -> None:
        self.event(f"- Saving {self.REQUIREMENTS_FILE}")
        with open(self.REQUIREMENTS_FILE, "w+") as f:
            f.write(f"# This file is managed automatically by {self.package_name}\n")
            f.write(package_installed + "\n")
            # We're intentionally leaving out ALL of the frozen requirements
            # as part of the point of this is to *simplify* the process
            # (the downside to this is that transitive dependencies can and will change without notice)

    def check_path(self) -> None:
        if not self.entrypoint_available():
            self.error(
                f'Could not find {self.package_name} in PATH\n\nAn simple solution is to add this to your .bash_profile/.zshrc:\nexport PATH="./.venv/bin:$PATH"'
            )
            raise Abort()

    def check_gitignore(self) -> None:
        if (
            os.path.exists(".git")
            and not self.gitignore_contains(self.VENV_NAME)
            and not self.gitignore_contains("/" + self.VENV_NAME)
        ):
            self.warn(
                f"- You should add {self.VENV_NAME} to your .gitignore so that it is not tracked by git"
            )

    def gitignore_contains(self, text: str) -> bool:
        if not os.path.exists(".gitignore"):
            return False

        with open(".gitignore") as f:
            for line in f:
                if line.strip().lower() == text.lower():
                    return True

        return False

    def get_installed_package(self) -> str:
        for line in (
            subprocess.check_output([f"{self.VENV_NAME}/bin/pip", "freeze"])
            .decode("utf-8")
            .splitlines()
        ):
            if re.match(r"^{}\W+".format(self.package_name), line.lower()):
                return line

        return ""

    def confirm(self, prompt: str) -> bool:
        return "y" in input(prompt).lower()

    def event(self, text: str) -> None:
        """Print in bold if we're in deubg (so regular output is distinguished)"""
        if self.debug:
            print("\033[1m" + text + "\033[0m")
        else:
            print(text)

    def warn(self, text: str) -> None:
        print("\033[33m" + text + "\033[0m")

    def error(self, text: str) -> None:
        print("\033[31m" + text + "\033[0m")

    def success(self, text: str) -> None:
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

    if "--update" in sys.argv:
        sys.argv.remove("--update")
        update = True
    else:
        update = False

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
        installer.run(reinstall=reinstall, update=update)
    except Abort:
        sys.exit(1)
