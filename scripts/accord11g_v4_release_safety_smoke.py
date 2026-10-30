"""Run selected current Honda Panda safety tests against a freshly built RELEASE libsafety.
This does not flash Panda or modify live comma. Only this process's libsafety loader is replaced.
"""
from opendbc.safety.tests.libsafety import libsafety_py
import pytest
release_lib = libsafety_py._build_libsafety(release=True)
libsafety_py.load(release_lib)
print("RELEASE_LIBRARY=", release_lib, flush=True)
print("RELEASE_LOADED=", libsafety_py.libpath, flush=True)
raise SystemExit(pytest.main([
 "-q",
 "opendbc_repo/opendbc/safety/tests/test_honda_mvl_stock.py",
 "opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py"
]))
