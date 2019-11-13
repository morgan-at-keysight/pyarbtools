from setuptools import setup, find_packages

setup(
    name='pyarbtools',
    version='0.0.14',
    author='Morgan Allison',
    author_email='morgan.allison@keysight.com',
    description='Keysight signal generator tools.',
    long_description='A collection of Python classes and functions that provide signal creation and instrument control capabilities for Keysight signal sources.',
    url='https://github.com/morgan-at-keysight/pyarbtools',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=['numpy', 'scipy'],
    # package_data={'pyarbtools':['package_data.dat']}
    license='GPL 3',
    classifiers=['License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',],
)
