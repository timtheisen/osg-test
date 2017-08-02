osg-test
========

[![Build Status](https://travis-ci.org/opensciencegrid/osg-test.svg?branch=master)](https://travis-ci.org/opensciencegrid/osg-test)

---

OSG Software's integration testing suite used in the nightly [VM tests](https://github.com/opensciencegrid/vm-test-runs).

Where to Write Tests
--------------------

All of the OSG Software automated tests are located in the `osg-test` software and package.

The software itself is in GitHub repository at <https://github.com/opensciencegrid/osg-test>; current code is kept in the `master` branch.

The software package is defined in our Subversion repository at `native/redhat/trunk/osg-test`.

### Directory Organization

The test software is written in Python and consists of:

-   A driver program, `osg-test`
-   A set of support libraries (Python modules) in `osgtest/library`
-   The tests themselves (also Python modules) in `osgtest/tests`
-   Extra files needed at runtime in `files`

The whole system uses the standard Python `unittest` framework to run. Note that all tests have to be compatible with Python 2.6; when reading the docs for `unittest`, keep note of when a feature was introduced.

### Test Sequence

During a test run, the test modules are run in sequence as follows:

| File                 | When                                          | Purpose                                                               |
|:---------------------|:----------------------------------------------|:----------------------------------------------------------------------|
| `special_user.py`    | Tests not suppressed, or explicitly requested | Add user (if asked), Check user, Set up mapfile                       |
| `special_install.py` | Packages given                                | Check repositories, Clean yum cache, Install packages                 |
| `test_NN_*.py`       | Tests not suppressed                          | Configure, Test, Tear down                                            |
| `special_cleanup.py` | Explicitly requested                          | Remove user (if added), Remove packages (if installed)                |

The `test_*` modules are organized roughly into three phases, based on the sequence number of the file:

| Test Files       | Purpose   |
|:-----------------|:----------|
| `test_[00-29]_*` | Set up    |
| `test_[30-69]_*` | Tests     |
| `test_[70-99]_*` | Tear down |

Coding Tips
-----------

It is important to know the basics of the Python `unittest` module; [read the documentation for it](http://docs.python.org/2.6/library/unittest.html). We build on top of the `unittest` module, by providing an `osgunittest` module that inherits from it.

### Basic Structure of a Test Module

Each test module must import the `osgunittest` library, plus whichever of the `osg-test` libraries are needed (conventionally with shortened aliases):

```python
import osgunittest

import osgtest.library.core as core
import osgtest.library.files as files
```

Then, a single test class is defined, deriving from `osgunittest.OSGTestCase`; the individual tests are sequentially numbered functions within the class:

```python
class TestFooBarBaz(osgunittest.OSGTestCase):

    def test_01_first_thing(self):
        # test stuff!

    def test_02_more(self):
        # test stuff!

    # Tests return (success) or raise (failure)
```

### Test Assertions

Within each test function, use the [TestCase object functions](http://docs.python.org/2.6/library/unittest.html#unittest.TestCase) to assert things that should be true:

```python
def test_99_example(self):
     result = do_something()
     self.assert_(result > 42, 'result too low')
     self.assertEqual(result, 57, 'result ok')
```

Be sure to learn and use all of the assertion functions, for greatest expressive power and clarity! For example, there are also:

-   `assertNotEqual`(*first*, *second*\[, *message*\])
-   `assertRaises`(*exception*, *callable*, …)

### Skipping Tests

There are two cases in which a test should be skipped, and they have different semantics in `osgunittest`:

1.  If the packages they depend on are not installed. This is called an `OkSkip`, since it does not indicate any sort of error.
2.  If the packages they depend on *are* installed, but required services were unavailable. This is called a `BadSkip`, since it indicates a cascading failure -- an error in a previous step that is causing problems in the current step.

One of the extensions that `osgunittest` adds to `unittest` is the ability to report on these kinds of failures.

The following `osgunittest` methods cause the test to be skipped with an `OkSkip` ( `OkSkipException` ):

- `skip_ok`(\[*message*=*None*\]):
  - skip, with optional message
- `skip_ok_if`(*expr*, \[*message*=*None*]):
  - skip if `expr` is True, with optional message
- `skip_ok_unless`(*expr*, \[*message*=*None*]):
  - skip if `expr` is False, with optional message

And the following `osgunittest` methods cause the test to be skipped with a `BadSkip` ( `BadSkipException` ):

- `skip_bad`(\[*message=None*\]):
  - skip, with optional message
- `skip_bad_if`(*expr*, \[*message*=*None*]):
  - skip if `expr` is True, with optional message
- `skip_bad_unless`(*expr*, \[*message*=*None*]):
  - skip if `expr` is False, with optional message

Note that the `OkSkip` methods are often not directly used, and convenience functions in `osgtest.core` are used instead.

#### Skipping Due to Missing Packages (OkSkip)

The following two patterns are used for skipping tests due to missing packages; use the simplest one for your case (or follow conventions of other tests):

Example 1: A single package with custom skip message

```python
def test_01_start_condor(self):
    core.skip_ok_unless_installed('condor',
                                  message='HTCondor not installed')
```

Example 2: A normal check of several packages at once:

```python
def test_02_condor_job(self):
    core.skip_ok_unless_installed('globus-gram-job-manager-condor',
                                  'globus-gram-client-tools',
                                  'globus-proxy-utils')
```

Note that old unit test code might be using the methods `core.rpm_is_installed()` or `core.missing_rpm()` for this purpose. These just printed a message if the test was to be skipped, but the test writer had to actually perform the skip manually.

The following patterns should be converted to match the first and second example, respectively:

Old Example 1:

```python
if not core.rpm_is_installed('condor'): # OLD CODE
    core.skip('not installed')
    return
```

Old Example 2:

```python
if core.missing_rpm('globus-gram-job-manager-condor', # OLD CODE
                    'globus-gram-client-tools',
                    'globus-proxy-utils'):
    return
```

**Note:** Add skip tests to **all** functions that depend on a particular package, not just the first one within a test module.

#### Skipping Due to Failure in Required Service (BadSkip)

Tests often require a service to be up and running. If the service is not running, then it is expected that the test will fail through no fault of the component being tested. These cascading failures often mask the root cause of the problem. In order to avoid that, we instead skip the test, and mark it as having been skipped due to a previous failure (a BadSkip). Note that these should be raised only *after* making sure the service has been installed.

The following examples show how this is done:

```python
core.skip_ok_unless_installed('globus-gram-job-manager-condor')
self.skip_bad_unless(core.state['condor.running-service'], message='HTCondor service not running')
```

```python
core.skip_ok_unless_installed( 'globus-gram-job-manager-pbs',
                               'globus-gram-client-tools',
                               'globus-proxy-utils',
                               'globus-gram-job-manager-pbs-setup-seg')

if (not core.state['torque.pbs-configured'] or
    not core.state['torque.pbs-mom-running'] or
    not core.state['torque.pbs-server-running'] or
    not core.state['globus.pbs_configured']):

    self.skip_bad('pbs not running or configured')
```

**Note:** Add skip tests to **all** functions that depend on a particular service, not just the first one within a test module.

### Running System Commands

Most tests run commands on the system; this is the nature of our testing environment. Thus, the test libraries have extra support for running system commands. Use these functions! Do not reinvent the wheel.

See the PyDoc for the `core` library for full documentation on the functions. Below are examples.

The basic system-call pattern:

```python
def test_99_made_up_example(self):
    command = ('/usr/bin/id','-u')
    status, stdout, stderr = core.system(command, True)
    fail = core.diagnose('id of test user', status, stdout, stderr)
    self.assertEqual(status, 0, fail) # Maybe more checks and assertions
```

In the most common case, you run the `core.system()` function, check its exit status against 0, and then possibly test its stdout and stderr for problems. There is a helper function for this common case:

```python
def test_01_web100clt(self):
    if core.missing_rpm('ndt'):
        return
    command = ('web100clt', '-v')
    stdout, stderr, fail = core.check_system(command, 'NDT client')
    result = re.search('ndt.+version', stdout, re.IGNORECASE)
    self.assert_(result is not None)
```

### Configuration and State

The test framework does not automatically preserve values across test modules, so you must do so yourself if needed. But, the test library does provide standard mechanisms for saving configuration values and system state.

Store all cross-module configuration values in `core.config` (a dictionary):

```python
def test_04_config_voms(self):
    core.config['voms.vo'] = 'osgtestvo'
    # ...
```

Record cross-module state values in `core.state` (a dictionary):

```python
def test_01_start_mysqld(self):
    core.state['mysql.started-server'] = False
    # Try to start MySQL service, raise on fail
    core.state['mysql.started-server'] = True
```

### Module-Wide Setup and Teardown

Sometimes a module needs certain operations to be done for setting up tests. For example, the tests for osg-configure involve importing the unit test modules provided by osg-configure itself, and need to add an entry to `sys.path`. This kind of setup should be put *inside* the test class; it will not get reliably run if it is only inside the module. Making separate test functions for the setup and teardown steps (named, for example, `test_00_setup` and `test_99_teardown`) is a good way of handling this.

Testing your changes
--------------------

Before you go and commit your changes, it's a good idea to make sure they don't break everything. Our [nightlies](http://vdt.cs.wisc.edu/tests/latest.html) run tests against the master version of osg-test so to avoid the embarassment of everyone knowing that your code is broken, you'll want to make sure your tests work!

### Fermicloud VMs

1.  Start a fermicloud VM and install the OSG RPMs, the latest build of `osg-test` and `osg-tested-internal`.
2.  Get rid of the old tests:
    ```
    # For RHEL 6, CentOS 6, and SL6
    [root@client ~]$ rm -rf /usr/lib/python2.6/site-packages/osgtest
    # For RHEL 7, CentOS 7, and SL7
    [root@client ~]$ rm -rf /usr/lib/python2.7/site-packages/osgtest
    ```
3.  `cd` into your clone of the `osg-test` repo and copy over your tests to your VM:
    ```
    # For RHEL 6, CentOS 6, and SL6 VMs
    [user@client ~]$ scp -r osgtest/ <VM HOSTNAME>:/usr/lib/python2.6/site-packages
    # For RHEL 7, CentOS 7, and SL7 VMs
    [user@client ~]$ scp -r osgtest/ <VM HOSTNAME>:/usr/lib/python2.7/site-packages
    ```
4.  Run the tests and monitor their output:
    ```
    [root@client ~]$ osg-test -vad > <OUTFILE>
    [root@client ~]$ tail -f <OUTFILE>
    ```

### VM Universe

It's a good idea to test your changes in the VM Universe if you've made big changes like adding tests or changing entire test modules. Otherwise, you can go ahead and skip this step.

1.  SSH to `osghost.chtc.wisc.edu`
2.  Prepare a test run:
    ```
    [user@client ~]$ osg-run-tests -sl <TEST COMMENT>
    ```
3.  `cd` into the directory that is indicated by the output of `osg-run-tests`
4.  Run `git diff master` from your clone of the `osg-test` repo to get the changes that you're interested in and fill `test-changes.patch` with these changes.
5.  Edit `test-parameters.yaml` so that the `sources` section reads:
    ```
    sources:
       - opensciencegrid:master; 3.3; osg-testing
    ```
6.  Start the tests:
    ```
    [user@client ~]$ condor_submit_dag master-run.dag
    ```
