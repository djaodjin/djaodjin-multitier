# -*- Makefile -*-

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= $(realpath .)
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin
CONFIG_DIR    ?= $(srcDir)
# XXX CONFIG_DIR should really be $(installTop)/etc/testsite
LOCALSTATEDIR ?= $(installTop)/var

installDirs   ?= install -d
installFiles  := install -p -m 644
NPM           ?= npm
PYTHON        := $(binDir)/python

ASSETS_DIR    := $(srcDir)/htdocs/static
RUN_DIR       ?= $(srcDir)
DB_NAME       ?= $(RUN_DIR)/db.sqlite

MANAGE        := TESTSITE_SETTINGS_LOCATION=$(CONFIG_DIR) RUN_DIR=$(RUN_DIR) $(PYTHON) manage.py

# Django 1.7,1.8 sync tables without migrations by default while Django 1.9
# requires a --run-syncdb argument.
# Implementation Note: We have to wait for the config files to be installed
# before running the manage.py command (else missing SECRECT_KEY).
RUNSYNCDB     = $(if $(findstring --run-syncdb,$(shell cd $(srcDir) && $(MANAGE) migrate --help 2>/dev/null)),--run-syncdb,)


install::
	cd $(srcDir) && $(PYTHON) ./setup.py --quiet \
		build -b $(CURDIR)/build install

install-conf:: $(DESTDIR)$(CONFIG_DIR)/credentials \
                $(DESTDIR)$(CONFIG_DIR)/gunicorn.conf


$(DESTDIR)$(CONFIG_DIR)/credentials: $(srcDir)/testsite/etc/credentials.conf
	[ -f $@ ] || \
		SECRET_KEY=`$(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'` ; \
		sed -e "s,\%(SECRET_KEY)s,$${SECRET_KEY}," $< > $@


$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf: $(srcDir)/testsite/etc/gunicorn.conf
	install -d $(dir $@)
	[ -f $@ ] || sed \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@


initdb: install-conf
	-rm -f $(srcDir)/db.sqlite $(srcDir)/example1.sqlite $(srcDir)/example2.sqlite
	cd $(srcDir) && $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && $(MANAGE) loaddata testsite/fixtures/test_data.json
	cd $(srcDir) && MULTITIER_DB_FILE=example1.sqlite $(MANAGE) migrate --database example1 --noinput
	cd $(srcDir) && MULTITIER_DB_FILE=example1.sqlite $(MANAGE) loaddata --database example1 testsite/fixtures/example1.json
	cd $(srcDir) && MULTITIER_DB_FILE=example2.sqlite $(MANAGE) migrate --database example2 --noinput
	cd $(srcDir) && MULTITIER_DB_FILE=example2.sqlite $(MANAGE) loaddata --database example2 testsite/fixtures/example2.json

doc:
	$(installDirs) docs
	cd $(srcDir) && sphinx-build -b html ./docs $(PWD)/docs
