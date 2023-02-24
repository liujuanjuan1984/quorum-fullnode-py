import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="quorum_fullnode_py",
    version="1.1.0",
    author="liujuanjuan1984",
    author_email="qiaoanlu@163.com",
    description="Python SDK for FullNode of QuoRum",
    keywords=["quorum_fullnode_py", "rumsystem", "quorum"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liujuanjuan1984/quorum_fullnode_py",
    project_urls={
        "Github Repo": "https://github.com/liujuanjuan1984/quorum_fullnode_py",
        "Bug Tracker": "https://github.com/liujuanjuan1984/quorum_fullnode_py/issues",
        "About Quorum": "https://github.com/rumsystem/quorum",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(exclude=["tests"]),
    python_requires=">=3.7",
    install_requires=[
        "requests",
    ],
)
