import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="playlistjockey",
    version="1.0.0",
    author="Robby Alberse",
    author_email="robalberse@gmail.com",
    description="Unlock innovative ways to experience playlists.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://robalberse.github.io/playlistjockey/",
    project_urls={
        'Source': "https://github.com/robalberse/playlistjockey",
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    license="LGPL-3.0-or-later",
    py_modules=["playlistjockey"]
)