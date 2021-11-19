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

- an initial install script through curl/Python (`curl -sSL https://raw.githubusercontent.com/dropseed/barrel/master/barrel/install.py | python3 - <package_name>` for now)
  - creates `.venv`
  - saves `requirements.txt`
- a self-updating process that can be included directly in your app
  - `<your_app> update`

Python 3 only.

## Alternatives

### pip by itself

### pipx

### poetry, pipenv, etc.

## Why?

Python is a great language, but managing dependencies either requires additional knowledge or third-party tools.
Both of these can be inconvenient for users who don't have a lot of experience with Python.
Barrel aims to a one-liner experience for using command line tools that fit the use-case.

## What it doesn't do

The primary goal of Barrel is to **simplify** the dependency installation/update process for people.
So it shouldn't come as a surprise that certain features you know from full-fledged dependency managers are intentionally missing.

### Freeze *all* dependency requirements

The `requirements.txt` won't include all of the pinned versions of indirect/transitive dependencies.
While that would help with the predictability of an install,
those details don't (and arguably *shouldn't*) matter to most people and can cause a lot of noise in automated dependency update tools.

If you're authoring a package that uses Barrel,
you should take extra care to specify the ranges of your dependencies that you know *work*,
and put a CI process in place to regularly test a fresh install just like your users would get.

### Lock to a specific Python version

Managing multiple Python versions is not for everyone.
There are tools and ways to do it,
but it can get complicated fast.

Barrel only works with Python 3 since [Python 2 was sunset in 2020](https://www.python.org/doc/sunset-python-2/).
This makes it easier.

Similar to the point on frozen requirements,
it should be the package authors responsiblity to define the range of Python3 versions you support and to make sure they work.
