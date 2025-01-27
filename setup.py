#! python
"""
author: FinX Capital Markets
purpose: Setup file for FinX Python Client
"""
from setuptools import setup

import os

setup(
    name="finx-io",
    version=os.getenv("FINX_VERSION"),
    description="Python client for FinX Platform APIs",
    url="https://github.com/FinX-IO/finx",
    author="FinX Capital Markets LLC",
    author_email="support@finx.io",
    license="MIT",
    install_requires=[
        "aiohttp",
        "aenum",
        "asgiref",
        "setuptools",
        "nest-asyncio",
        "numpy",
        "pandas",
        "plotly",
        "pydantic",
        "pytest",
        "requests",
        "scipy",
        "websocket-client",
        "websockets",
        "pylint",
        "sphinx",
        "sphinx-autoapi",
        "autodoc_pydantic",
        "sphinx-rtd-theme",
    ],
    zip_safe=False,
)
