from setuptools import setup, find_packages

setup(
    name="eum-agenticAI",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pytest",
        "requests",
        "httpx",
    ],
) 