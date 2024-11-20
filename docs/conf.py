# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from sphinx.application import Sphinx

project = "FinX SDK"
copyright = "2024, FinX Capital Markets"
author = "FinX Capital Markets"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autoapi.extension",
    "sphinxcontrib.autodoc_pydantic",
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autosummary',
    'sphinx_mdinclude',
    'sphinx.ext.autodoc',
]
source_suffix = ['.rst', '.md']

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False
autosummary_generate = True
autodoc_preserve_defaults = True
autodoc_member_order = 'bysource'
autodoc_default_flags = [
    'members',
    # 'private-members', 'special-members', 'show-inheritance'
]


def autodoc_process_docstring(*args, **kwargs):
    print('DOCSTRING', *args, **kwargs)


def autodoc_skip_member(app, what, name, obj, skip, options):
    new_skip = what in ['data', 'method'] and '_' in name.split('.')[-1][0]
    print('SKIP MEMBER: ', what, name, skip, new_skip)
    return skip or new_skip


def setup(app: Sphinx):
    app.connect('autoapi-skip-member', autodoc_skip_member)


autoapi_dirs = ["../src/"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "piccolo_theme"
html_static_path = ["_static"]
