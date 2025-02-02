from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="queuelib",
    version="1.7.0",
    license="BSD",
    description="Collection of persistent (disk-based) and non-persistent (memory-based) queues",
    long_description=Path("README.rst").read_text(encoding="utf-8"),
    long_description_content_type="text/x-rst",
    author="Scrapy project",
    author_email="info@scrapy.org",
    url="https://github.com/scrapy/queuelib",
    packages=find_packages(),
    package_data={
        "queuelib": ["py.typed"],
    },
    platforms=["Any"],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
