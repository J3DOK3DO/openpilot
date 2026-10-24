def pytest_configure(config):
  config.addinivalue_line(
    "markers", "SIMULATED_TEST_TRUST: uses an ephemeral in-memory simulated production key; never release signing")
