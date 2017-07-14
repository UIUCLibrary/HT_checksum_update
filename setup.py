from setuptools import setup
import update_yml

setup(
    name=update_yml.__title__,
    version=update_yml.__version__,
    packages=['update_yml'],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    url=update_yml.__url__,
    license='',
    author=update_yml.__author__,
    author_email=update_yml.__author_email__,
    entry_points={
        "console_scripts": [
            "udhtchecksum = update_yml.cli:main"
        ]
    },
    description=update_yml.__description__
)
