from setuptools import setup, find_packages

setup(
    name="queuelib",
    version="1.6.2",
    license="BSD",
    description="Collection of persistent (disk-based) and non-persistent (memory-based) queues",
    long_description=open("README.rst").read(),
    author="Scrapy project",
    author_email="info@scrapy.org",
    url="https://github.com/scrapy/queuelib",
    packages=find_packages(),
    platforms=["Any"],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
