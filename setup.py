""" SetupTool Entry Point """
import sys
import setuptools

from distutils.spawn import find_executable

with open("README.md", "r") as fh:
    long_description = fh.read()


install_requirements = [
    "grpcio", 
    "grpcio-tools", 
    "googleapis-common-protos"
]


def get_setuptools_ver():
    ver_components = setuptools.__version__.split(".")[:3]
    return tuple([int(x) for x in ver_components])


if get_setuptools_ver() < (40, 1, 0):
    print(
        "Setuptools version too old, v40.1.0 and above required. Might be able to upgrade with"
    )
    print("\tpip install --upgrade setuptools")
    print("Or use provided setup.sh script.")
    sys.exit(1)


# if sys.version_info < (3, 7):
#     install_requirements.append("importlib_resources")
#     install_requirements.append("wheel")

# import pkg_resources

# from grpc_tools import _protoc_compiler
# from grpc_tools.command import *
# import os 

# # bfproto_dir = os.path.abspath('./proto')
# bfproto_dir = os.path.join(os.path.dirname(__file__), './proto')
# bfproto_file = os.path.join(bfproto_dir, 'bfrt_helper/pb2/bfruntime.proto')

# if not os.path.exists(bfproto_dir):
#     raise Exception(f'Could not find {bfproto_dir}')

# if not os.path.exists(bfproto_file):
#     raise Exception(f'Could not find {bfproto_file}')

# x = '/home/gawen/Development/packet-broker/bfrt-helper/proto'
# x = '/home/gawen/Development/packet-broker/bfrt-helper/proto/bfrt_helper/pb2/bfruntime.proto'

# proto_include = pkg_resources.resource_filename('grpc_tools', '_proto')
# protoc_args = [
#     f'--proto_path={bfproto_dir}',
#     f'--proto_path={proto_include}',
#     '--proto_path=./python-api-common-protos',
#     '--python_out=.',
#     '--grpc_python_out=.',
#     f'{bfproto_file}', 
# ]
# print('python -m grpc_tools.protoc {}'.format(' '.join(protoc_args)))
# for f in protoc_args:
#     print(f)
# print()

# protoc_args = [argument.encode('utf-8') for argument in protoc_args]
# _protoc_compiler.run_main(protoc_args)

# build_package_protos(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proto'))

setuptools.setup(
    name="bfrt_helper",
    version="1.0",
    author="APS Networks GmbH",
    author_email="support@aps-networks.com",
    description="Helper library for the Barefoot Runtime gRPC interface.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/APS-Networks/bfrt-helper",
    packages=setuptools.find_namespace_packages(exclude=["test"]),
    # setup_requires=[
    #     'protobuf_distutils'
    # ],
    # options={
    #     # See below for details.
    #     'generate_py_protobufs': {
    #         'source_dir': 'proto',
    #         'extra_proto_paths': [
    #             'python-api-common-protos'
    #         ],
    #         'output_dir': 'bfrt_helper/pb2',  # default '.'
    #         # 'output_dir': 'bfrt_helper/pb2',  # default '.'
    #         'proto_files':       [
    #             'proto/bfrt_helper/pb2/bfruntime.proto'
    #         ],
    #         'protoc': find_executable("protoc"),
    #     },
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires=">=3.6",
    install_requires=install_requirements,
)
