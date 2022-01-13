# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------


project = 'Barefoot Runtime gRPC Helper'
copyright = '2021, APS Networks GmbH'
author = 'APS Networks GmbH'

# The full version, including alpha/beta/rc tags
release = '1.0.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
#
# Napoleon allows the use of Numpy style docstrings.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage', 
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    
    # 'sphinx.ext.graphviz',
    'sphinxcontrib.email',
    # 'recommonmark',
    'sphinx.ext.autosectionlabel',
    # 'autodocsumm',
    'myst_parser'
]


autosectionlabel_prefix_document = True

source_suffix = ['.rst', '.md']
# autodoc_member_order = 'bysource'
add_module_names = False
autodoc_default_options = {
    'show-inheritance': True,
    # 'members': True,
    'member-order': 'bysource',
    # 'special-members': '__le__,__ge__,__lt__,__gt__,__eq__,__and__,__or__,__iter__',
    'undoc-members': False,
    # 'exclude-members': '__weakref__',
    # 'autosummary': True,
    # 'autosummary-nosignatures': True,
    'inherited-members': False,
}

# autoclass_content = 'class'

autodoc_default_flags = ['members']
autosummary_generate = True

# autosectionlabel_prefix_document = True

autodoc_inherit_docstrings = True

napoleon_google_docstring = True
napoleon_numpy_docstring = False
# napoleon_include_init_with_doc = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
# napoleon_include_special_with_doc = True
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'renku'
# html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_favicon = '_static/favicon.ico'
html_logo = '_static/logo.png'
html_theme_options = {
    # 'navigation_depth': 4,
    'collapse_navigation': False
}
html_css_files = [
    '_static/blockquote.css',
]


# latex_elements = {
#   'extraclassoptions': 'openany,oneside'
# }

from bfrt_helper.fields import Field, StringField
import inspect

'''A vain attempt to ignore ``__new__`` I don't think it worked, hence the
more complicated code used to process signatures.'''
def skip_new(app, what, name, obj, would_skip, options):
    if name in [
        '__dict__', 
        '__module__', 
        '__weakref__', 
        '__doc__',
        '__str__',
        '__repr__',
        '__slots__',
        '__init__',
        '__new__'
    ]:
        return True
    if what != 'class':
        # if not issubclass(obj, Field):
        #     return False
        # f = Field()
        # base_props = [x for x in obj.__dict__]

        return False

    if obj == None:
        return True

    return would_skip

import re


'''Pre-processes displayed signatures.

There are two deficiencies as I see it wrt Sphinx and document generation.

A minor gripe is that the signatures include the full package and module path
when referring to another object type, which is annoying since, in most cases,
Sphinx is more than capable of creating a reference to such classes in it's
absence. The solution here is to simply strip ``/bfrt_helper\..*?\,/`` from
the string.

Secondly, and more annoyingly, there are issues with displaying the proper
signatures of derived classes when the base defines ``__new__``. You will
find that for a given signature ``__new__(*args, **kwargs)``, each subclass
will have documented the same. THe solution here is to lookup the actual class,
inspect and retrieve the signature, substituting ``self, `` for nothing. Then
the module stripping routine is applied to clean everything up. Since the
``Field`` object is the only class that does this, we selectively choose it.

'''
def autodoc_process_signature(
        app,
        what,
        name,
        obj,
        options,
        signature,
        return_annotation):

    if what == 'class':
        if getattr(obj, '__init__') is not None:
            if issubclass(obj, Field):
                signature = str(inspect.signature(obj.__init__))
                signature = signature.replace('self, ', '')
        # signature = re.sub(r'bfrt_helper\..*?\.', '', signature)

        return signature, return_annotation
    if what == 'method':
        if return_annotation is not None:
            signature = re.sub(r'bfrt_helper\..*?\.', '', signature)
            return signature, return_annotation.split('.')[-1]

    return signature, return_annotation



def setup(app):
    app.connect('autodoc-process-signature', autodoc_process_signature)
    # app.connect('autodoc-skip-member', skip_new)
    app.add_css_file('css/blockquote.css')
    app.add_css_file('css/font.css')
