"""Setup script for AI Context Manager."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-context-manager",
    version="0.1.0",
    author="AI Context Manager Team",
    author_email="team@ai-context-manager.com",
    description="Export codebases for AI analysis with intelligent file selection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-context-manager/ai-context-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pathspec>=0.11.0",
    ],
    extras_require={
        "yaml": ["PyYAML>=6.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-context=ai_context_manager.cli:app",
            "acm=ai_context_manager.cli:app",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_context_manager": ["templates/*.json"],
    },
)