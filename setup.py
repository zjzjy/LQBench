from setuptools import setup, find_packages

setup(
    name="LQBench",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "pandas",
        "matplotlib",
        "numpy",
        "tqdm"
    ],
) 