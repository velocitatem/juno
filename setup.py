from setuptools import setup, find_packages
import os
import re

# Read the version from __init__.py
with open(os.path.join("juno_manager", "__init__.py"), "r") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read the requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines() if line.strip()]

# Read the long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="juno-manager",
    version=version,
    description="JupyterLab Virtual Environment Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Daniel Rosel",
    author_email="daniel@alves.world",
    url="https://github.com/velocitatem/juno",
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "juno-manager=juno_manager.cli:run_cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.7",
)
