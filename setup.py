from setuptools import setup, find_packages

# Read requirements from requirements.txt and filter out Git URLs
with open('requirements.txt') as f:
    all_requirements = f.read().splitlines()
    requirements = [req for req in all_requirements if not req.startswith("git+")]

setup(
    name="alcopt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'alc-ui=run_app:main',
        ],
    },
)