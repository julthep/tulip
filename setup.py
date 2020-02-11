import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tulip-rdf",
    version="0.1.0",
    author="Julthep Nandakwang",
    author_email="julthep@nandakwang.com",
    description="TULIP RDF vocabulary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/julthep/tulip",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)