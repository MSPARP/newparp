import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

CHANGES = ""

setup(
    name="charat2",
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        "flask",
        "sqlalchemy",
    ],
    entry_points="""\
    [console_scripts]
    charat2_init_db = charat2.model:init_db
    """,
)

