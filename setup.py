# coding=utf-8
from setuptools import setup, find_packages

setup(
    name="QCMaker",
    version="0.1",
    author="Thibaut Le Gouic",
    author_email="thibautlg@gmail.com",
    description="Création et correction automatiques de QCM",
    keywords="qcm correction",
    packages=find_packages(),
    long_description=open('README.txt').read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Teacher",
        "Programming Language :: Python :: ",
    ],
    requires=['django', 'matplotlib','numpy'],
)
