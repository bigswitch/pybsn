from setuptools import setup

setup(name='pybsn',
    version='0.2.0',
    description="pybsn is a python interface to Big Switch Networks' products",
    url='https://github.com/floodlight/pybsn',
    author='Jason Parraga, Rich Lane, Andreas Wundsam',
    author_email='Sovietaced@gmail.com, Rich.Lane@bigswitch.com, Andreas.Wundsam@bigswitch.com',
    license='ECLIPSE',
    packages=['pybsn'],
    zip_safe=False,
    install_requires=[
    "requests >= 2.3.0"
    ],
    scripts=['bin/pybsn-repl', 'bin/pybsn-schema'])
