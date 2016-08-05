from setuptools import setup, find_packages

import ampy


setup(
    name='ampy',
    version=ampy.__version__,
    description='Adafruit MicroPython tool is a command line tool to interact with a MicroPython board over a serial connection.',
    url='https://github.com/adafruit/Adafruit_MicroPython_Tool',
    author='Tony DiCola',
    author_email='tdicola@adafruit.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='micropython',
    packages=find_packages(),
    install_requires=['click', 'pyserial'],
    entry_points={
        'console_scripts': [
            'ampy=ampy.cli:cli',
        ],
    },
)
