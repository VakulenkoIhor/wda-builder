from setuptools import setup

setup(
    name='wda-builder',
    version='1.0.0',
    packages=['wda_builder'],
    url='',
    license='MIT',
    author='Ihor Vakulenko',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'wdabuild = wda_builder:wda_build',
        ]
    },
    install_requires=['argparse>=1.4']
)
