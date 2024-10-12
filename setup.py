from setuptools import setup, find_packages


# Reading the contents of requirements.txt file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name='domain_manager',
    version='1.0.0',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'domain-manager=src.main:main',
        ],
    },
    author='Aram SEMO',
    author_email='aram.semo@asemo.pro',
    description='A tool to manage domains based on Docker events.',
    url='https://github.com/arasemco/DomainManager',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Freeware',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
