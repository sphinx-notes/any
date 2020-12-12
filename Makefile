LANG=en_US.UTF-8

MAKE = make
PY   = python3

.PHONY: doc
doc:
	rm doc/_build -rf
	$(MAKE) -C doc/

.PHONY: dist
dist: setup.py
	$(PY) setup.py sdist
