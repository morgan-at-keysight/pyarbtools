from setuptools import setup, find_packages

setup(
    name='pyarbtools', version='0.1.0',
    author='Morgan Allison', author_email='morgan.allison@keysight.com',
    description='Keysight signal generator tools.',
    long_description='A collection of Python classes and functions that provide signal creation and instrument control capabilities for Keysight signal sources.',
    url='https://github.com/morgan-at-keysight/pyArbTools',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=['numpy', 'scipy'],
    # package_data={'pyarbtools':['package_data.dat']}
    license='GPL 3',
    classifiers=['License :: GNU GPL 3 License',
        'Programming Language :: Python :: 3.6',]
)
