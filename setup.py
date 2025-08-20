from setuptools import setup, find_packages

setup(
    name="smartlinks-autopilot",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        # Add other dependencies here
    ],
    python_requires=">=3.7",
)
