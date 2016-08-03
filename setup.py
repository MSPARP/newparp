import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

CHANGES = ""

setup(
    name="newparp",
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        "bcrypt",
        "flask",
        "sqlalchemy",
    ],
    entry_points="""\
    [console_scripts]
    newparp_init_db = newparp.model.init_db:init_db
    """,
    test_suite="nose2.collector.collector",
    tests_require=["exam", "nose2"],
)

