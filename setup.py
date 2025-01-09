from setuptools import setup, find_packages
from ap.version import __version__

# Function to read dependencies from Pipfile
def read_requirements():
    import toml  # Ensure you install this dependency with `pip install toml`

    pipfile_data = toml.load('Pipfile')
    packages = pipfile_data.get('packages', {})
    return [f"{pkg}{ver if ver != '*' else ''}" for pkg, ver in packages.items()]

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
