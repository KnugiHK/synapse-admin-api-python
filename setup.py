import setuptools
from re import search

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("synapse_admin/__init__.py", encoding="utf8") as f:
    version = search(r'__version__ = "(.*?)"', f.read()).group(1)

setuptools.setup(
    name="matrix-synapse-admin",
    version=version,
    author="KnugiHK",
    author_email="info@knugi.com",
    description="A Python wrapper for Matrix Synapse admin API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KnugiHK/synapse-admin-api-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Communications :: Chat",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators"
    ],
    python_requires='>=3.7',
    install_requires=[
       'httpx>=0.18.2'
    ]
)
