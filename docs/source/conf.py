import sys
from pathlib import Path

sys.path.insert(0, str(Path('../..').resolve()))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ptv-timetable'
copyright = '%Y pizza1016'
author = 'pizza1016'
release = '0.4.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx"
]

templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
    "members": True,
    "member-order": "groupwise",
    "show-inheritance": True
}

autodoc_typehints = "description"
autodoc_use_type_comments = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "aiolimiter": ("https://aiolimiter.readthedocs.io/en/stable/", None)
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    "body_max_width": "auto",
    "page_width": "90%"
}
html_static_path = ['_static']
