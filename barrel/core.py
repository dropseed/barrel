from .install import Installer


def update(package_name: str, entrypoint_name: str = "") -> None:
    installer = Installer(package=package_name, entrypoint_name=entrypoint_name)
    installer.update()
