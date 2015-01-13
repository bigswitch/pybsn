from setuptools import setup

setup(name='pybsn',
    version='0.1.0',
    description="pybbsn is a python interface to Big Switch Network's products",
    url='https://github.com/Sovietaced/pybsn',
    author='Jason Parraga, Rich Lane',
    author_email='Sovietaced@gmail.com, Rich.Lane@bigswitch.com',
    license='ECLIPSE',
    packages=['pybsn'],
    zip_safe=False,
    install_requires=[
    "requests >= 2.3.0"
    ],
    scripts=['bin/pybsn-repl', 'bin/pybsn-schema'])
