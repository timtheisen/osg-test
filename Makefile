# Makefile for osg-test


# ------------------------------------------------------------------------------
# Release information: Update for each release
# ------------------------------------------------------------------------------

PACKAGE := osg-test
VERSION := 0.0.8


# ------------------------------------------------------------------------------
# Other configuration: May need to change for a release
# ------------------------------------------------------------------------------

SBIN_FILES := osg-test
INSTALL_SBIN_DIR := usr/sbin

CA_CERT_DIR := ca-certificate
CA_CERT_FILES := $(CA_CERT_DIR)/4eca18ce.*
INSTALL_CA_CERT_DIR := etc/grid-security/certificates

SHARE_DIR := files
CERT_FILE := $(SHARE_DIR)/usercert.pem
CERT_KEY := $(SHARE_DIR)/userkey.pem
TEST_FILES := $(SHARE_DIR)/test_*
INSTALL_SHARE_DIR := usr/share/osg-test

PYTHON_DIR := osgtest
PYTHON_FILES := $(PYTHON_DIR)/*.py

DIST_FILES := $(SBIN_FILES) $(CA_CERT_DIR) $(SHARE_DIR) $(PYTHON_DIR) Makefile


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

.PHONY: _default distclean install dist upstream

_default:
	@echo "There is no default target; choose one of the following:"
	@echo "make install DESTDIR=path     -- install files to path"
	@echo "make dist                     -- make a distribution source tarball"
	@echo "make upstream [UPSTREAM=path] -- install source tarball to upstream cache rooted at path"


distclean:
	rm -f *.tar.gz
ifneq ($(strip $(DIST_DIR_PREFIX)),) # avoid evil
	rm -fr $(DIST_DIR_PREFIX)*
endif

install:
ifeq ($(strip $(DESTDIR)),)
	@echo "Error: make install requires DESTDIR to be defined"
else
	mkdir -p $(DESTDIR)/$(INSTALL_SBIN_DIR)
	install -p -m 0755 $(SBIN_FILES) $(DESTDIR)/$(INSTALL_SBIN_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_CA_CERT_DIR)
	install -p -m 0644 $(CA_CERT_FILES) $(DESTDIR)/$(INSTALL_CA_CERT_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0644 $(CERT_FILE) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0400 $(CERT_KEY) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	install -p -m 0644 $(TEST_FILES) $(DESTDIR)/$(INSTALL_SHARE_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_DIR)
	install -p -m 0644 $(PYTHON_FILES) $(DESTDIR)/$(INSTALL_PYTHON_DIR)/$(PYTHON_DIR)
endif


dist: $(TARBALL_NAME)
$(TARBALL_NAME): $(DIST_FILES)
	$(eval TEMP_DIR := $(shell mktemp -d -p . $(DIST_DIR_PREFIX)XXXXXXXXXX))
	mkdir -p $(TEMP_DIR)/$(TARBALL_DIR)
	cp -pr $(DIST_FILES) $(TEMP_DIR)/$(TARBALL_DIR)/
	tar czf $(TARBALL_NAME) -C $(TEMP_DIR) $(TARBALL_DIR)
	rm -rf $(TEMP_DIR)


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
