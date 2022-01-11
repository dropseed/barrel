# Barrel

<img src="https://user-images.githubusercontent.com/649496/144511332-90651fbb-826c-4776-9bce-05586b1a1d02.png" width="100" height="100" align="right" />

**Python command line tools that are easy to install, repo-isolated, and update themselves.**

Users install your package with:

```console
$ curl -sSL https://barrel.dev/install.py | python3 - <pypi_package_name>
```

And update it with:

```console
$ <cli_name> update
```

- [Overview](#overview)
- [What Barrel is](#what-barrel-is)
- [How Barrel works](#how-barrel-works)
- [Barrel for package authors](#barrel-for-package-authors)
- [What Barrel doesn't do](#what-barrel-doesnt-do)
- [Alternatives](#alternatives)

## Overview

Python can be a great language for writing command line tools,
but your users shouldn't have to be Python experts to use them.

For tools that are *globally* installed,
people tend to do things like `pip install --user <package>`,
[write a custom installation script](https://github.com/python-poetry/poetry/blob/cbbd92ceb5938a43a1f4666cdaf9599c74650442/get-poetry.py),
or install and use a wrapper like [pipx](https://github.com/pypa/pipx/).

This works when you intend to use the same version of the CLI no matter what you're working on.
But there are other things like static site generators and automation tools that should be installed specifically into a user's *repository*.
The version installed needs to be isolated and pinned,
so you can use the same tools on multiple repos/projects without worrying about update conflicts and forcing them all to use the same version.

There are obviously ways to deal with this today (see [alternatives](#alternatives)),
but they all require a certain amount of Python-ecosystem knowledge that your users may not have.
Especially if your CLI is written in Python,
but the user doesn't actually use Python when interacting with it.

## What Barrel is

Barrel is an installation script,
embeddable package,
and set of conventions for installing an isolated and versioned command line tool into a repo.
As a bonus, Barrel makes it easy for you to have a self-updating CLI.

The goal is to *simplify* the process (especially for non-Pythonistas) and provide a developer experience that doesn't suck.
It does this by being a lightweight wrapper around standard, known conventions that can be used as a "one-liner".

Using well-known conventions like `requirements.txt` also allows standard CI/CD workflows and other services/tools to "just work",
without knowing or caring about Barrel itself.
This makes it automatically compatible with hosting services like Netlify,
and dependency management automation like Dependabot.

## How Barrel works

The initial install of a command line tools is done with a script.
A curl -> Python command is the easiest way to do this,
and doesn't require *any* additional dependencies besides Python 3 (which your CLI requires anyway).

```console
$ curl -sSL https://barrel.dev/install.py | python3 - <pypi_package_name>
```

This will create a virtual environment at `.venv` and `requirements.txt` file.
The `.venv` should be in `.gitignore` but the `requirements.txt` should be committed.
The install script will help point out these details for people that aren't familiar with them.

The `requirements.txt` file will look something like this and effectively ["pins"](https://www.python.org/dev/peps/pep-0440/#version-matching) the version in use until an update is made:

```txt
# This file is managed automatically by <package>
<package>==2.3.0
```

Once installed, updates can be done two ways.

1) Barrel is integrated into the package/CLI itself, providing a command like `<package> update`.
This is the most user-friendly way to do it,
since they already have your CLI installed and don't have to remember or save the curl command.
2) But if you don't include Barrel in your package,
you can always run the curl command again to update the package (using the `--reinstall` option).

The only caveat at this point is that `.venv/bin/` needs to be in the user's `PATH`,
or they need to use `./.venv/bin/<package>` directly.
The install script will help point this out and how it can be done (ex. `export PATH="./.venv/bin:$PATH"`).

## Barrel for package authors

To use Barrel for the installation process,
you just need a published package that is your CLI.

You can copy [install.py](https://github.com/dropseed/barrel/blob/master/barrel/install.py) to your own repo or site,
but the we always keep an up-to-date hosted version at https://barrel.dev/install.py.

Your documentation should tell users how to use the curl command (including your package name as the argument).

```console
$ curl -sSL https://barrel.dev/install.py | python3 - <pypi_package_name>
```

You *should* add "barrel" as a dependency in your package and provide a self-updating experience.
To do this, you just need to call the `update` function with the name of your package.
You can add it to your CLI like this example using [click](https://github.com/pallets/click):

```python
import barrel


@click.command()
def update():
    """Update your version of combine"""
    barrel.update("combine")
```

If you don't add "barrel" as a dependency,
then you'll need to tell users to run the curl command again to update with the `--reinstall` option.

```console
$ curl -sSL https://barrel.dev/install.py | python3 - <pypi_package_name> --reinstall
```

Things to know:

- Barrel supports Python 3 only
- Barrel expects your package to be the only direct dependency the user needs to install (i.e. their `requirements.txt` will only end up with your package in it -- [nothing else](#freeze-all-dependency-requirements))
- Barrel expects your package to have an entrypoint (by default this should be the same as the package name)

## What Barrel doesn't do

The primary goal of Barrel is to *simplify* the dependency installation/update process for people.
So it shouldn't come as a surprise that certain features you know from full-fledged dependency managers are intentionally missing.

### Freeze *all* dependency requirements

The `requirements.txt` won't include all of the pinned versions of indirect/transitive dependencies.
While that would help with the predictability of an install,
those details don't (and arguably *shouldn't*) matter to most people and can cause a lot of noise in automated dependency update tools.

If you're authoring a package that uses Barrel,
you should take extra care to specify the ranges of your dependencies that you know *work*,
and put a CI process in place to regularly test a fresh install just like your users would get.

### Lock to a specific Python version

Barrel won't save the Python version it used during the install,
and it won't force everyone on the repo to use the same Python version.

Managing multiple Python versions is not for everyone.
There are tools and ways to do it,
but it can get complicated fast.

Barrel only works with Python 3 since [Python 2 was sunset in 2020](https://www.python.org/doc/sunset-python-2/).
This makes it easier.

Similar to the point on frozen requirements,
it should be the package authors responsiblity to define the range of Python3 versions you support and to make sure they work.
[Use a matrix in your CI tests to stay on top of it.](https://github.com/dropseed/barrel/blob/fae14a440e503ee67ec81da053a47c2ec8439ecb/.github/workflows/test.yml#L8-L15)

## Alternatives

### pip by itself

Barrel is a wrapper around standard pip processes and conventions,
so you can obviously do the same thing with pip directly.
The problem is, there are a series of steps that people either have to already know or have scripted.
There are a lot of decisions to make along the way and you can easily lose people just by having an overly complicated install process for someone who isn't familiar with Python.

Barrel essentially does these steps for a new install:

```console
$ python3 -m venv .venv
$ ./.venv/bin/pip install <package>
$ ./.venv/bin/pip freeze | grep <package> > requirements.txt
```

These steps for a fresh install of an existing repo:

```console
$ python3 -m venv .venv
$ ./.venv/bin/pip install -r requirements.txt
```

And these steps for update:

```console
$ ./.venv/bin/pip install -U <package>
$ ./.venv/bin/pip freeze | grep <package> > requirements.txt
```

Barrel makes the install step (new or existing) a curl one-liner,
and the update step as simple as `<package> update`.

### pipx

On the surface, [pipx](https://github.com/pypa/pipx/) is pretty similar in goals.
The difference is that pipx is aimed at tools that are installed *globally* on a user's machine.
This is not exactly what you want if your package needs to be versioned to a specific user's repo.

If you try to use a globally installed command across multiple repos,
you run into problems when a new version of the command is released and new features are added/removed that aren't compatible with *all* of your repos (build command changed syntax, YAML config settings changed, etc.).
The only solution you have is to update all of them at once,
which can be a pretty unpleasant experience depending on the changes required.

### poetry, pipenv, etc.

In a lot of ways, Barrel is intended to be a simpler alternative to these.
Both [Poetry](https://github.com/python-poetry/poetry) and [Pipenv](https://github.com/pypa/pipenv) can be used for installing a specific version of a Python package into a repo.
But they come with a lot of other baggage that you simply don't need for a single-dependency repo.

Both require you to install the tool itself first (which is a process of its own),
and can force other decisions like locking to a specific Python version,
new commands to learn,
and extra headaches if poetry/pipenv themselves break!
Which does happen (surprisinglyg frequently in the case of Pipenv) and can require a lot of difficult troubleshooting.
Barrel largely avoids this by doing basic `pip` commands and `requirements.txt` flows that are unlikely to have any problems.
