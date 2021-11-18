# Barrel

Deliver Python command line tools that don't require users to be Python experts.

Designed for things like static site generators and automation tools where the user-code isn't actually written in Python,
but the tool should be installed *inside* the repo and pinned to a specific version.
Otherwise people tend to install these things globally,
which falls apart as soon as you use the tool on multiple repos and different repos start using different versions of the same (globally installed) tool.

The users gets an installation and update experience that doesn't require deep knowledge of virtual environments, pip, poetry/pipenv, or Python dependencies,
but provides the same benefits of conventions that CI and other build tools already recognize.

Barrel uses standard Python filenames and conventions,
which means other services and tools will work just like they do with standard pip + requirements.txt setups.
This way you get the best of both worlds --
a structure that automatically works with other services (CI, Netlify, Dependabot, etc.),
while being wrapped in a user-friendly DX for people unfamiliar with Python.

Barrel roughly works like this:

- an initial install script through curl/Python
  - creates `.venv`
  - saves `requirements.txt`
- a self-updating process that can be included directly in your app
  - `<your_app> update`

## Alternatives

### pip by itself

### pipx

### poetry, pipenv, etc.

## Why?

Python is a great language, but managing dependencies either requires additional knowledge or third-party tools.
Both of these can be inconvenient for users who don't have a lot of experience with Python.
Barrel aims to a one-liner experience for using command line tools that fit the use-case.
