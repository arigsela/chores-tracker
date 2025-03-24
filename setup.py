from setuptools import setup, find_packages

setup(
    name="chores-tracker",
    version="0.1",
    description="A chores tracking system for families",
    author="Chores Tracker Team",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.103.1",
        "uvicorn>=0.22.0",
        "sqlalchemy>=2.0.19",
        "alembic>=1.11.1",
        "pydantic>=2.1.1",
        "pydantic-settings>=2.0.3",
        "aiosqlite>=0.19.0",
        "pymysql>=1.1.0",
        "email-validator>=2.1.0",
        "passlib==1.7.4",
        "bcrypt==3.2.2",
        "python-jose>=3.3.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "httpx>=0.24.1",
        ],
    },
    python_requires=">=3.9",
) 