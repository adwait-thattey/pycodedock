import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pycodedock",
    version="0.0.1",
    author="Adwait Thattey",
    author_email="adwaitthattey@gmail.com",
    description="A module that allows you to programatically run python scripts safely inside docker containers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adwait-thattey/pycodedock",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 2 - Pre-Alpha",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
    ],
)
