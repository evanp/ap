from setuptools import setup, find_packages

setup(
    name='ap',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ap=ap.main:main',  # "ap" is the command, "ap.main:main" refers to the main function in your main.py
        ],
    },
    install_requires=[
        'requests',
        'webfinger',
        'oauthlib',
        'requests_oauthlib',
        'tabulate',
    ],
    author='Evan Prodromou',
    author_email='evan@prodromou.name',
    description='A simple command-line ActivityPub client',
    license='GPLv3',
    keywords=['activitypub', 'client', 'cli', 'social', 'fediverse', 'socialweb', 'api'],
)