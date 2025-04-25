from setuptools import setup, find_packages

setup(
    name="analytics_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.2",
        "uvicorn==0.27.1",
        "sqlalchemy[asyncio]==2.0.27",
        "asyncpg==0.29.0",
        "python-dotenv==1.0.1",
        "alembic==1.13.1",
        "pydantic==2.6.1",
        "pydantic-settings==2.1.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
    ],
) 