# Copyright (c) 2024 Joel Torres
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://opensource.org/license/mit.

from setuptools import setup

with open("README.md") as f:
    doc = f.read()

setup(
    name="prombin",
    description="CLI tool for installing/updating the latest Prometheus precompiled binary",
    long_description=doc,
    long_description_content_type="text/markdown",
    author="Joel Torres",
    author_email="joetor5@icloud.com",
    url="https://github.com/joetor5/prombin",
    license="MIT",
    platforms="any",
    py_modules=["prombin"],
    install_requires=[
        "beautifulsoup4==4.12.3",
        "requests==2.32.3",
        "tqdm==4.66.5"
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts":[
            "prombin=prombin:main"
        ]
    },
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Console"
    ]
)
