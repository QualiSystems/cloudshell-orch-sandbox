import sys

from setuptools import setup, find_packages
import os

with open(os.path.join('version.txt')) as version_file:
    version_from_file = version_file.read().strip()

with open('requirements.txt') as f_required:
    required = f_required.read().splitlines()

with open('test_requirements.txt') as f_tests:
    required_for_tests = f_tests.read().splitlines()

if (sys.version_info < (3,0)):
    required_for_tests.append("mock")

setup(
        name="cloudshell-orch-core",
        author="Quali",
        author_email="support@qualisystems.com",
        packages=find_packages(),
        package_data={'': ['*.txt']},
        tests_require=required_for_tests,
        #test_suite='nose.collector',
        #test_suite="tests.tests.tomer",
        install_requires=required,
        version=version_from_file,
        include_package_data=True,
        keywords="sandbox cloud cloudshell",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.0",
            "Topic :: Software Development :: Libraries",
            "License :: OSI Approved :: Apache Software License",
        ]
)