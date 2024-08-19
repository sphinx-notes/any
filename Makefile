# This file is generated from sphinx-notes/cookiecutter.
# You need to consider modifying the TEMPLATE or modifying THIS FILE.

LANG = en_US.UTF-8

MAKE  = make
PY    = python3
RM    = rm -rf
GIT   = git
OPEN  = xdg-open

# Build sphinx documentation.
.PHONY: docs
docs:
	$(MAKE) -C docs/

# View sphinx HTML documentation in browser.
.PHONY: view
view:
	$(OPEN) docs/_build/html/index.html

.PHONY: clean
clean:
	$(MAKE) -C docs/ clean
	$(RM) dist/

.PHONY: clean
fmt:
	ruff format src/

# Run unittest.
.PHONY: test
test:
	$(PY) -m unittest discover -s tests -v

# Build distribution package, for "install" or "upload".
.PHONY: dist
dist: pyproject.toml clean
	$(PY) -m build

# Install distribution package to user directory.
#
# NOTE: It may breaks your system-level packages, use at your own risk.
.PHONY: install
install: dist
	export PIP_BREAK_SYSTEM_PACKAGES=1 # required by Python 3.11+, see PEP-668
	$(PY) -m pip install --user --no-deps --force-reinstall dist/*.whl

# Publish wheel to PyPI offical server <https://pypi.org/> when you want to
# You should have a PyPI account and have PyPI token configured.
#
# See also https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives
.PHONY: upload
upload: dist
	$(PY) -m twine upload --repository pypi $</*

# Same to the aboved "upload" target, but this publishs to PyPI test server
# <https://test.pypi.org/>.
.PHONY: upload-test
upload-test: dist
	$(PY) -m twine upload --repository testpypi $</*

# Keep up to date with the latest template.
# See also https://github.com/sphinx-notes/cookiecutter.
.PHONY: update-template
update-template:
	$(PY) -m cruft update

.PHONY: update-template-done
update-template-done:
	$(GIT) commit -m "chore: Update project template to sphinx-notes/cookiecutter@$(shell jq -r '.commit' .cruft.json | head -c8)"

# Update project version.
.PHONY: bump-version
bump-version:
	@echo -n "Please enter the version to bump: "
	@read version && $(PY) -m cruft update --variables-to-update "{ \"version\" : \"$$version\" }"

# EXTRA TARGETS START

# EXTRA TARGETS END
