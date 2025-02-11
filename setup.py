from setuptools import setup, find_packages

setup(
    name="trd-cli",
    version="0.1.1",
    description="Treatment Resistant Depression Database Command Line Interface",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Matt Jaquiery",
    author_email="matt.jaquiery@dtc.ox.ac.uk",
    url="https://github.com/OxfordRSE/trd-cli",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "pandas",
        "pytest",
        "pytest-cov",
        "codecov",
        "redcap",
    ],
    entry_points={
        "console_scripts": [
            "trd-cli=trd_cli.main:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
