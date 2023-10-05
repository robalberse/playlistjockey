import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="playlistjockey",
    version="1.0.0",
    author="Robby Alberse",
    description="Unlock innovative ways to experience playlists.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GNU GPLv3",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.9",
    py_modules=["playlistjockey"]
)