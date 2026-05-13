import os
import sys
import yaml

# Add paths to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../test')))

# Load metadata from CITATION.cff
cff_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../CITATION.cff'))
with open(cff_path, 'r', encoding='utf-8') as f:
    cff_data = yaml.safe_load(f)

project = cff_data.get('title')
version = cff_data.get('version')
release = version

# Format authors
author_list = []
for auth in cff_data.get('authors'):
    name = f"{auth.get('given-names')} {auth.get('family-names')}".strip()
    if name: author_list.append(name)
author = ", ".join(author_list)

copyright = f'2026, {author}'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']

# PDF generation settings
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'preamble': r'''
\usepackage{newunicodechar}
\newunicodechar{⪩}{>>}
\newunicodechar{🖹}{[FILE]}
\newunicodechar{🖿}{[DIR]}
''',
}
