rom setuptools import setup
import yaml

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("../../moduleversion.yaml") as f:
    data = yaml.full_load(f)
    major = str(data["major"])
    minor = str(data["minor"])
    module_version = major + "." + minor

setup(
    name="demoapp",
    description="The seer demonstration is awesome.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="demoapp seer sut container mocksystemundertest",
    version=module_version,
    author="The mobius team at MATRIX/RAS",
    author_email="svteng_team_mobius@matrix.com",
    url="https://artifactory.rspringob.local/artifactory/pypi-virtual/demoapp",
    python_requires=">=3.6",
    packages=["demoapp"],
    package_dir={"demoapp": "demoapp"},
    package_data={"demoapp": ["data/*.yaml"]},
    install_requires=["PyYAML"],
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
