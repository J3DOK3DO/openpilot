"""Scoped ``sys.modules`` stubs for host-only StarPilot tests.

Several tests import real controllers against synthetic ``openpilot.*`` / ``cereal``
modules. Installing those stubs permanently (``sys.modules[...] = ...`` at import
time) leaks them into every module collected afterwards: ``ParamKeyType`` and
``ACCELERATION_DUE_TO_GRAVITY`` then vanish from ``openpilot.common.params`` /
``openpilot.common.constants`` and unrelated test modules fail to import.

``scoped_module_stubs`` installs the stubs only while the controller under test is
imported, then restores ``sys.modules`` and drops the project modules that were
imported against the stubs, so later imports see the real modules again. Classes
and functions already imported keep the stub-bound globals they were built with.
"""
import contextlib
import sys
from types import ModuleType

_MISSING = object()
_SCALARS = (bool, int, float, complex, str, bytes, type(None))


def _stub_ids(stubs):
  ids = set()
  for module in stubs.values():
    ids.add(id(module))
    for value in vars(module).values():
      if not isinstance(value, _SCALARS):
        ids.add(id(value))
  return ids


def _tainted_modules(candidates, stubs):
  """Candidates whose globals reference a stub, transitively through each other."""
  stub_ids = _stub_ids(stubs)
  tainted = set()
  changed = True
  while changed:
    changed = False
    for name in candidates:
      if name in tainted:
        continue
      for value in list(vars(sys.modules[name]).values()):
        owner = value.__name__ if isinstance(value, ModuleType) else getattr(value, "__module__", None)
        if id(value) in stub_ids or owner in tainted:
          tainted.add(name)
          changed = True
          break
  return tainted


def _forget(name):
  module = sys.modules.pop(name, None)
  parent_name, _, child = name.rpartition(".")
  parent = sys.modules.get(parent_name)
  if parent is not None and module is not None and getattr(parent, child, None) is module:
    delattr(parent, child)


@contextlib.contextmanager
def scoped_module_stubs(stubs, purge=()):
  """Install ``stubs`` ({module name: module}) for the duration of the block.

  ``purge`` names project modules that must be imported fresh against the stubs
  inside the block: any real copy is set aside on entry and put back on exit, and
  the stub-bound copy never outlives the block. Other modules imported inside the
  block that reference a stub (directly or through a purged module) are detected
  and dropped on exit as well.
  """
  saved = {name: sys.modules.get(name, _MISSING) for name in stubs}
  set_aside = {name: sys.modules.pop(name) for name in purge if name in sys.modules}
  before = set(sys.modules)
  sys.modules.update(stubs)
  try:
    yield
  finally:
    candidates = [n for n in sys.modules if n not in before and n.startswith("openpilot.") and n not in stubs]
    for name in sorted(_tainted_modules(candidates, stubs) | {n for n in purge if n in sys.modules}):
      _forget(name)
    for name, previous in saved.items():
      if previous is _MISSING:
        sys.modules.pop(name, None)
      else:
        sys.modules[name] = previous
    for name, previous in set_aside.items():
      sys.modules[name] = previous
      parent_name, _, child = name.rpartition(".")
      if parent_name in sys.modules:
        setattr(sys.modules[parent_name], child, previous)
