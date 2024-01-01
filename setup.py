from setuptools import setup, find_packages
from ap.version import __version__

# Function to read the contents of the requirements file
def read_requirements():
    with open('requirements.txt') as req:
        return req.read().splitlines()

setup(
    name='ap',
    version=__version__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ap=ap.main:main',  # "ap" is the command, "ap.main:main" refers to the main function in your main.py
        ],
    },
    install_requires=read_requirements(),
    author='Evan Prodromou',
    author_email='evan@prodromou.name',
    description='A simple command-line ActivityPub client',
    license='GPLv3',
    keywords=['activitypub', 'client', 'cli', 'social', 'fediverse', 'socialweb', 'api'],
)