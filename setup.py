"""Setup module."""
from setuptools import setup

with open('README.md', 'r', encoding='UTF-8') as file:
    README = file.read()

setup(
    name='falcontyping',
    version='0.2.8',
    url='https://github.com/abdelrahman-t/falcontyping',
    author='Abdurrahman Talaat <abdurrahman.talaat@gmail.com>',
    author_email='abdurrahman.talaat@gmail.com',
    packages=['falcontyping', 'falcontyping.base', 'falcontyping.middleware', 'falcontyping.typedjson'],
    include_package_data=True,
    python_requires='>=3.7.0',
    install_requires=['falcon', 'wrapt'],

    description='Add type hints support to Falcon with Pydantic and Marshmallow integration',
    long_description=README,
    long_description_content_type='text/markdown',

    keywords=['falcon', 'typing', 'hints', 'mypy', 'pydantic', 'marshmallow'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ],

    project_urls={
        'Documentation': 'https://github.com/abdelrahman-t/falcontyping'
    },
)
