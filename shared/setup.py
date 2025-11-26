from setuptools import setup, find_packages

setup(
    name="siete-cx-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlmodel>=0.0.24",
        "sqlalchemy>=2.0.41",
        "pydantic>=2.0",
        "pydantic-settings>=2.7.0",
        "passlib>=1.7.4",
    ],
    python_requires=">=3.10",
)
