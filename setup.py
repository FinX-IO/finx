import os
from setuptools import setup

setup(name='finx-io',
      version=os.getenv("FINX_VERSION"),
      description='Python client for FinX Platform APIs',
      url="https://github.com/FinX-IO/finx",
      author='FinX Capital Markets LLC',
      author_email='support@finx.io',
      license='MIT',
      packages=['aiohttp>=3.8.4',
        'aenum>=3.1.15',
        'asgiref>=3.8.1',
        'setuptools>=67.0.0',
        'nest-asyncio>=1.5.6',
        'numpy>=1.25.0',
        'pandas>=2.0.2',
        'plotly>=5.15.0',
        'pydantic>=2.3.0',
        'pytest>=6.2.5',
        'requests>=2.31.0',
        'scipy>=1.10.1',
        'websocket-client>=1.6.0',
        'websockets>=11.0.3',
        'pylint>=3.3.1',
        'sphinx>=8.1.3',
        'sphinx-autoapi>=3.3.3',
        'autodoc_pydantic>=2.2.0',
        'sphinx-rtd-theme>=3.0.2'],
      zip_safe=False)
