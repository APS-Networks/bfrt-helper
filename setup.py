""" SetupTool Entry Point """
import sys
import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


# install_requirements = [
#     "grpcio",
#     "grpcio-tools",
#     "googleapis-common-protos"
# ]


def get_setuptools_ver():
    ver_components = setuptools.__version__.split(".")[:3]
    return tuple([int(x) for x in ver_components])


if get_setuptools_ver() < (40, 1, 0):
    print(
        "Setuptools version too old, v40.1.0 and above required. ",
        "Might be able to upgrade with"
    )
    print("\tpip install --upgrade setuptools")
    print("Or use provided setup.sh script.")
    sys.exit(1)


name = 'bfrt_helper'
version = '1.0'
release = '1.0.0'

setuptools.setup(
    name=name,
    version=release,
    author="APS Networks GmbH",
    author_email="support@aps-networks.com",
    description="Helper library for the Barefoot Runtime gRPC interface.",
    long_description=long_description,
    url="https://github.com/APS-Networks/bfrt-helper",
    packages=['bfrt_helper'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ]
)
