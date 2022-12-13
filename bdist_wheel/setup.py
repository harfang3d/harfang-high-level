from setuptools import setup, Distribution
from codecs import open  # to use a consistent encoding
import os, shutil

here = os.path.abspath(os.path.dirname(__file__))


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths


if os.path.exists("HarfangHighLevel/Harfang"):
    shutil.rmtree("HarfangHighLevel/Harfang")

shutil.copytree("Harfang_x64", "HarfangHighLevel/Harfang", dirs_exist_ok=True)

extra_files = package_files("HarfangHighLevel")

# get version
with open(os.path.join(here, "version.txt"), encoding="utf-8") as f:
    version_string = f.read()

# get the long description from the relevant file
with open(os.path.join(here, "DESCRIPTION.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="HarfangHighLevel",
    version=version_string,
    description="High Level functions to use with Harfang",
    long_description=long_description,
    url="https://www.harfang3d.com",
    author="NWNC HARFANG",
    author_email="contact@harfang3d.com",
    license="Other/Proprietary License",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Topic :: Scientific/Engineering :: Visualization",
        "Operating System :: Microsoft",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
    ],
    keywords="2d 3d multimedia development engine realtime rendering design visualization simulation physics vr virtual reality python lua opengl opengles directx",
    packages=["HarfangHighLevel"],
    include_package_data=True,
    package_data={"HarfangHighLevel": extra_files},
    python_requires=">=3.8",
    install_requires=["harfang==3.2.4", "tqdm", "py7zr"],
)
