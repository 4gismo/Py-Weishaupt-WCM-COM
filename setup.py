import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="weishaupt-wcm-com",
    version="0.0.13",
    author="Philip Schmiegelt, Pieter Hamels, Gero Strobel",
    author_email="philip@schmiegelt.it, pieter@hamels.be, 4gismo@gmx.de",
    description="Interfacing the Weishaupt WCM-COM module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/phamels/Py-Weishaupt-WCM-COM",
    install_requires=["requests"],
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
