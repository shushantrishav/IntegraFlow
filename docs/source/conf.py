# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
sys.path.insert(0, os.path.abspath('../../')) # Adjust this path to point to your project's root.
                                           # From docs/source, ../../ goes up to project_root/
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'IntegraFlow'
copyright = '2025, shushant rishav'
author = 'shushant rishav'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon', # This is good practice even if primarily using reST, for flexibility
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx', # If you answered 'y' to intersphinx
    'sphinx.ext.todo',        # If you answered 'y' to todo
    'sphinx.ext.coverage',    # If you answered 'y' to coverage
    'sphinx.ext.ifconfig',    # If you answered 'y' to ifconfig
    'sphinx.ext.autosummary', # Very useful for generating summary tables
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Options for autodoc
autodoc_default_options = {
    'members': True,
    'undoc-members': False, # Set to True if you want to document members without docstrings
    'private-members': False, # Set to True if you want to document private members (starting with _)
    'special-members': '__init__', # Include __init__ docstrings
    'show-inheritance': True,
    'member-order': 'bysource', # 'alphabetical', 'groupwise', or 'bysource'
    'exclude-members': '__weakref__' # Exclude specific members if needed
}

# Ensure __init__ docstring appears with the class
autoclass_content = "both"