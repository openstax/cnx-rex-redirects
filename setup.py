# -*- coding: utf-8 -*-
from pathlib import Path
from setuptools import setup, find_packages


here = Path(__file__).parent


def _filter_requirement(req):
    req = req.strip()
    # skip comments and dash options (e.g. `-e` & `-r`)
    return bool(req and req[0] not in '#-')


def read_from_requirements_txt(filepath):
    f = here / filepath
    with f.open('r') as fb:
        return tuple([
            x.strip()
            for x in fb
            if _filter_requirement(x)
        ])

install_requires = read_from_requirements_txt('requirements.txt')
tests_require = []
extras_require = {
    'test': tests_require,
}

# Boilerplate arguments
SETUP_KWARGS = dict(
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    packages=find_packages(),
    include_package_data=True,
)

# Note, this is not to be released to PyPI. It's for interal usage only

setup(
    name='cnx-rex-redirects',
    version='1.0.1',
    author='OpenStax',
    url="https://github.com/openstax",
    license='LGPL',
    py_modules=['rex_redirects'],
    entry_points="""\
    [console_scripts]
    rex_redirects = rex_redirects:main
    """,
    **SETUP_KWARGS,
)
