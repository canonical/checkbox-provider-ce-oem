# This is a file to introducing OP-TEE(Open Source - Trusted Execution Environment) test jobs.

## id: ce-oem-optee/device-node
  This job will check if OP-TEE node (teepriv0 and tee0) have been probed.
  And it relies on the manifest "has_optee" to be true.

## id: ce-oem-optee/xtest-check
  This job will check if xtest is in gadget snap. Since xtest and TA rely on the same signing key with optee-os and optee-client. Therefore, xtest will be build-in in gadget snap.
  However, if you intend to use your own build optee-test, you can assign the checkbox config variable to make this job to use specific tool.
  Checkbox config variable "OPTEE_TOOL" should be gaven a full applications name.
  Includes SNAP name and APP name if it as a SNAP, otherwise the the APP name should be fine.
  e.g. SNAP named "optee-test" and APP name "xtest".
    OPTEE_TOOL=optee-test.xtest
  e.g. APP named "xtest".
    OPTEE_TOOL=xtest

## id: ce-oem-optee-test-list
  This is a resource job will generate a list of the optee-test agenest the optee-test.json.(Please check the section about *Test cases for optee-test*).
  And it will be include *regression* and *benchmark* of optee-test.
  The checkbox config variable "OPTEE_CASES" allows you to give a path of *optee-test.json* if needed. Otherwise, it will use the default JSON file in the provier.
  Please make sure the file can be accessed by checkbox.
  e.g. OPTEE_CASES=/home/user/optee-test.json

## id: ce-oem-optee-test-list-pkcs11
  This is a resource job will generate a list of the optee-test agenest the optee-test.json.(Please check the section about *Test cases for optee-test*).
  And it will be include *pkcs11* of optee-test.
  The checkbox config variable "OPTEE_CASES" allows you to give a path of *optee-test.json* if needed. Otherwise, it will use the default JSON file in the provier.
  Please make sure the file can be accessed by checkbox.
  e.g. OPTEE_CASES=/home/user/optee-test.json

## Test coverage
  We have covered the default tests of optee-test, which include: 
  - Benchmark
  - Regression
  - PKCS11
  
  For the *Benchmark* and *Regression* tests, TA (Trusted Applications) need to be installed before the test

  For the *PKCS11* tests, there are no specific requirements.

## Test cases for optee-test (optee-test.json)
  We parse the source of xtest that in optee-test. And dump it into *optee-test.json*. And we have a [python script](https://git.launchpad.net/~rickwu4444/+git/tools/tree/parse_optee_test_cases) to do it offline. 