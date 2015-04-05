# -*- Makefile -*-

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= .
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin

PYTHON        := $(binDir)/python
installDirs   ?= install -d

install::
	cd $(srcDir) && $(PYTHON) ./setup.py --quiet \
		build -b $(CURDIR)/build install

install-conf:: credentials

credentials: $(srcDir)/testsite/etc/credentials
	[ -f $@ ] || \
		SECRET_KEY=`python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'` ; \
		sed -e "s,\%(SECRET_KEY)s,$${SECRET_KEY}," $< > $@

initdb: install-conf
	-rm -f db.sqlite3 example1.sqlite3 example2.sqlite3
	cd $(srcDir) && $(PYTHON) ./manage.py migrate --noinput
	cd $(srcDir) && $(PYTHON) ./manage.py loaddata testsite/fixtures/test_data.json
	cd $(srcDir) && MULTITIER_DB_FILE=example1.sqlite3 $(PYTHON) ./manage.py migrate --database example1 --noinput
	cd $(srcDir) && MULTITIER_DB_FILE=example1.sqlite3 $(PYTHON) ./manage.py loaddata --database example1 testsite/fixtures/example1.json
	cd $(srcDir) && MULTITIER_DB_FILE=example2.sqlite3 $(PYTHON) ./manage.py migrate --database example2 --noinput
	cd $(srcDir) && MULTITIER_DB_FILE=example2.sqlite3 $(PYTHON) ./manage.py loaddata --database example2 testsite/fixtures/example2.json

doc:
	$(installDirs) docs
	cd $(srcDir) && sphinx-build -b html ./docs $(PWD)/docs
