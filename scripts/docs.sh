#!/bin/bash
# Script to generate HTML documentation using Sphinx

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

source "${HERE}/init.sh"

echo "Generating documentation..."

if [ ! -d "${HERE}/../docs" ]; then
	echo "Initializing Sphinx documentation directory..."
	mkdir -p "${HERE}/../docs"
fi

# Ensure _static exists
mkdir -p "${HERE}/../docs/_static"

# Set Sphinx configuration
cat <<-EOF > "${HERE}/../docs/conf.py"
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
	EOF

cat <<-EOF > "${HERE}/../docs/index.rst"
	.. Fuzzy Expert System documentation master file

	BurnoutExys Documentation
	=========================

	.. toctree::
	   :maxdepth: 2
	   :caption: Contents:

	   modules
	   tests

	Indices and Search
	==================

	* :ref:\`genindex\`
	* :ref:\`modindex\`
	* :ref:\`search\`
	EOF

# Automatically generate module API docs from source
cd "${HERE}/../src" || exit 1
sphinx-apidoc -f -M -H "Application Packages" -o ../docs/ .

# Automatically generate module API docs from tests
cd "${HERE}/../test" || exit 1
sphinx-apidoc -f -M -H "Application Test Suites" --tocfile tests -o ../docs/ .

# Build HTML docs
cd "${HERE}/../" || exit 1
# Set PYTHONPATH so autodoc can find all modules during build
export PYTHONPATH="${HERE}/../src:${HERE}/../test"
sphinx-build -b html docs/ docs/_build/html
echo "Documentation generated at docs/_build/html/index.html"

# Build LaTeX docs
sphinx-build -b latex docs/ docs/_build/latex || echo "Warning: Failed to generate LaTeX sources."

# Try to build PDF
if cd docs/_build/latex 2>/dev/null; then
	if command -v latexmk &> /dev/null; then
		make all-pdf && echo "Successfully built PDF from LaTeX" || echo "Warning: Failed to build PDF from LaTeX"
        mkdir -p ../pdf && cp *.pdf ../pdf
	else
		echo "latexmk not found, skipping PDF compilation."
	fi
else
	echo "Warning: LaTeX build directory not found, skipping PDF build."
fi

exit 0