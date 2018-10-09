from setuptools import setup, find_packages

setup(
    name='pyarbtools', version='0.1.0',
    description='Keysight signal generator tools.',
    long_description='pyArbTools is a collection of Python classes and functions that provide basic signal creation, instrument configuration, and waveform download capabilities for Keysight signal sources.',
    url='https://github.com/morgan-at-keysight/pyArbTools',
    author='Morgan Allison', author_email='morgan.allison@keysight.com',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=['numpy', 'scipy'],
    # package_data={'pyarbtools':['package_data.dat']}
    entry_points={'console_scripts':['hello=example_package.cli:say_hello',]},
    license='GPL 3',
    classifiers=['License :: GNU GPL 3 License',
        'Programming Language :: Python :: 3.6',]
)