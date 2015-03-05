# Makefile for osg-test


# ------------------------------------------------------------------------------
# Release information: Update for each release
# ------------------------------------------------------------------------------

PACKAGE := osg-test
VERSION := 1.4.24


# ------------------------------------------------------------------------------
# Other configuration: May need to change for a release
# ------------------------------------------------------------------------------

SBIN_FILES := osg-test
INSTALL_SBIN_DIR := usr/sbin

SHARE_DIR := files
OPENSSL_EXT_FILE := $(SHARE_DIR)/openssl-cert-extensions.conf
OSG_CA_FILES := $(SHARE_DIR)/OSG-Test-CA.*
TEST_FILES := $(SHARE_DIR)/test_*
GRATIA_TEST_FILES := $(SHARE_DIR)/gratia/*
TARBALL_TEST_FILES := $(SHARE_DIR)/tarball/*
INSTALL_SHARE_DIR := usr/share/osg-test
GRATIA_FILES_DIR := $(INSTALL_SHARE_DIR)/gratia
TARBALL_FILES_DIR := $(INSTALL_SHARE_DIR)/tarball

PYTHON_ROOT_DIR := osgtest
PYTHON_ROOT_FILES := $(PYTHON_ROOT_DIR)/*.py
PYTHON_LIB_DIR := $(PYTHON_ROOT_DIR)/library
PYTHON_LIB_FILES := $(PYTHON_LIB_DIR)/*.py
PYTHON_TEST_DIR := $(PYTHON_ROOT_DIR)/tests
PYTHON_TEST_FILES := $(PYTHON_TEST_DIR)/*.py
PYTHON_TARBALL_TEST_DIR := $(PYTHON_ROOT_DIR)/tarball_tests
PYTHON_TARBALL_TEST_FILES := $(PYTHON_TARBALL_TEST_DIR)/*.py

DIST_FILES := $(SBIN_FILES) $(SHARE_DIR) $(PYTHON_ROOT_DIR) Makefile


# ------------------------------------------------------------------------------
# Hack in a location for a downloadable bootstrap script
# ------------------------------------------------------------------------------

BOOTSTRAP_NAME := bootstrap-osg-test
BOOTSTRAP_DIR := /p/vdt/public/html/native
BOOTSTRAP_PATH := $(BOOTSTRAP_DIR)/$(BOOTSTRAP_NAME)


# ------------------------------------------------------------------------------
# Internal variables: Do not change for a release
# ------------------------------------------------------------------------------

DIST_DIR_PREFIX := dist_dir_
TARBALL_DIR := $(PACKAGE)-$(VERSION)
TARBALL_NAME := $(PACKAGE)-$(VERSION).tar.gz
UPSTREAM := /p/vdt/public/html/upstream
UPSTREAM_DIR := $(UPSTREAM)/$(PACKAGE)/$(VERSION)
INSTALL_PYTHON_DIR := $(shell python -c 'from distutils.sysconfig import get_python_lib; print get_python_lib()')


# ------------------------------------------------------------------------------

.PHONY: _default distclean install dist upstream check

_default:
	@echo "There is no default target; choose one of the following:"
	@echo "make install DESTDIR=path     -- install files to path"
	@echo "make dist                     -- make a distribution source tarball"
	@echo "make upstream [UPSTREAM=path] -- install source tarball to upstream cache rooted at path"
	@echo "make check                    -- use pylint to check for errors"


distclean:
	rm -f *.tar.gz
ifneq ($(strip $(DIST_DIR_PREFIX)),) # avoid evil
	rm -fr $(DIST_DIR_PREFIX)*
endif

install:
	mkdir -p $(DESTDIR)/$(INSTALL_SBIN_DIR)
	install -p -m 0755 $(SBIN_FILES) $(DESTDIR)/$(INSTALL_SBIN_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0644 $(OPENSSL_EXT_FILE) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0644 $(OSG_CA_FILES) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0644 $(TEST_FILES) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	mkdir -p $(DESTDIR)/$(GRATIA_FILES_DIR)
	install -p -m 0644 $(GRATIA_TEST_FILES) $(DESTDIR)/$(GRATIA_FILES_DIR)
	mkdir -p $(DESTDIR)/$(TARBALL_FILES_DIR)
	install -p -m 0755 $(TARBALL_TEST_FILES) $(DESTDIR)/$(TARBALL_FILES_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_ROOT_DIR)
	install -p -m 0644 $(PYTHON_ROOT_FILES) $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_ROOT_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_LIB_DIR)
	install -p -m 0644 $(PYTHON_LIB_FILES) $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_LIB_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_TEST_DIR)
	install -p -m 0644 $(PYTHON_TEST_FILES) $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_TEST_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_TARBALL_TEST_DIR)
	install -p -m 0644 $(PYTHON_TARBALL_TEST_FILES) $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_TARBALL_TEST_DIR)

$(TARBALL_NAME): $(DIST_FILES)
	$(eval TEMP_DIR := $(shell mktemp -d -p . $(DIST_DIR_PREFIX)XXXXXXXXXX))
	mkdir -p $(TEMP_DIR)/$(TARBALL_DIR)
	cp -pr $(DIST_FILES) $(TEMP_DIR)/$(TARBALL_DIR)/
	sed -i -e 's/##VERSION##/$(VERSION)/g' $(TEMP_DIR)/$(TARBALL_DIR)/osg-test
	tar czf $(TARBALL_NAME) -C $(TEMP_DIR) $(TARBALL_DIR)
	rm -rf $(TEMP_DIR)

dist: $(TARBALL_NAME)

upstream: $(TARBALL_NAME)
ifeq ($(shell ls -1d $(UPSTREAM) 2>/dev/null),)
	@echo "Must have existing upstream cache directory at '$(UPSTREAM)'"
else ifneq ($(shell ls -1 $(UPSTREAM_DIR)/$(TARBALL_NAME) 2>/dev/null),)
	@echo "Source tarball already installed at '$(UPSTREAM_DIR)/$(TARBALL_NAME)'"
	@echo "Remove installed source tarball or increment release version"
else
	mkdir -p $(UPSTREAM_DIR)
	install -p -m 0644 $(TARBALL_NAME) $(UPSTREAM_DIR)/$(TARBALL_NAME)
	rm -f $(TARBALL_NAME)
endif
	install -p -m 0755 $(BOOTSTRAP_NAME) $(BOOTSTRAP_PATH)

check:
	pylint -E osg-test $(PYTHON_LIB_FILES) $(PYTHON_TEST_FILES) $(PYTHON_TARBALL_TEST_FILES)

