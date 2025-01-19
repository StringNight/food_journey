from setuptools import setup, find_packages

setup(
    name="food_journey_backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "asyncpg",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "aiofiles",
        "pytest",
        "pytest-asyncio",
        "httpx",
        "slowapi"
    ],
    python_requires=">=3.8",
) 