import pmmutils, os

from setuptools import setup, find_packages

with open("README.rst", "r") as f:
    long_descr = f.read()

__version__ = None
if os.path.exists("VERSION"):
    with open("VERSION") as handle:
        for line in handle.readlines():
            line = line.strip()
            if len(line) > 0:
                __version__ = line
                break

setup(
    name=pmmutils.__package_name__,
    version=__version__,
    description=pmmutils.__description__,
    long_description=long_descr,
    url=pmmutils.__url__,
    author=pmmutils.__author__,
    author_email=pmmutils.__email__,
    license=pmmutils.__license__,
    packages=find_packages(),
    python_requires=">=3.10",
    keywords=["pmmutils"],
    install_requires=[
        "GitPython",
        "pathvalidate",
        "psutil",
        "python-dotenv",
        "requests",
        "tqdm"
    ],
    project_urls={
        "Documentation": "https://github.com/meisnate12/pmmutils",
        "Funding": "https://github.com/sponsors/meisnate12",
        "Source": "https://github.com/meisnate12/pmmutils",
        "Issues": "https://github.com/meisnate12/pmmutils/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ]
)
