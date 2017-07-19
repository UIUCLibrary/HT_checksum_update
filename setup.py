from setuptools import setup
import hathi_checksum

setup(
    name=hathi_checksum.__title__,
    version=hathi_checksum.__version__,
    packages=['hathi_checksum'],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    url=hathi_checksum.__url__,
    license='University of Illinois/NCSA Open Source License',
    author=hathi_checksum.__author__,
    author_email=hathi_checksum.__author_email__,
    entry_points={
        "console_scripts": [
            "udhtchecksum = hathi_checksum.__main__:main"
        ]
    },
    description=hathi_checksum.__description__
)
