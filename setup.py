from setuptools import setup

setup(name='pybsn',
    version='0.3.2',
    description="pybsn is a python interface to Big Switch Networks' products",
    url='https://github.com/floodlight/pybsn',
    author='Jason Parraga, Rich Lane, Andreas Wundsam, Andre Kutzleb',
    author_email='Sovietaced@gmail.com, Rich.Lane@bigswitch.com, Andreas.Wundsam@arista.com, Andre.Kutzleb@arista.com',
    license='ECLIPSE',
    packages=['pybsn'],
    zip_safe=False,
    install_requires=[
        "requests >= 2.3.0",
        "IPython >= 7.9",
        "traitlets >= 4.3.3",
    ],
    tests_require=[
        "responses >= 0.10.6"
    ],
    scripts=['bin/pybsn-repl', 'bin/pybsn-schema'],
    test_suite="test",
)
