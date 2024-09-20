from setuptools import setup, find_packages

setup(
    name="junos_upgrader",
    version="1.0.0",
    author="Andrew Southard",
    author_email="andsouth44@gmail.com",
    description="A application to upgrade JunOS",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/andsouth44/junos_upgrader",
    packages=find_packages(),
    install_requires=[
        "junos_eznc == 2.7.1",
        "lxml == 5.3.0",
        "pytest == 8.3.2",
        "setuptools == 58.0.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
