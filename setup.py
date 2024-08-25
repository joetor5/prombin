from setuptools import setup

with open("README.md") as f:
    doc = f.read()

setup(
    name="prombin",
    description="Prometheus tool for installing/updating to the latest binary",
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
    entry_points={
        "console_scripts":[
            "prombin=prombin:main"
        ]
    },
    classifiers=[
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP"
    ]
)
