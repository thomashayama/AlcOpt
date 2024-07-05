from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="alcopt",
    version="0.0.1",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'alc-ui=run_app:main',
        ],
    },
)