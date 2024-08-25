from setuptools import setup, find_packages

setup(
    name="amp_lib",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "Pillow",
    ],
    author="Aradrareness",
    author_email="",
    description="A client library for interacting with AMP services",
    # long_description=open("README.md").read(),
    # long_description_content_type="text/markdown",
    url="https://github.com/ARadRareness/AMP",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
