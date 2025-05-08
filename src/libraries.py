import os

_DEBUG_OR_TEST = False

_USE_THREADING = os.environ.get("OBOE_USE_THREADING", True)
_USE_ASYNCIO = os.environ.get("OBOE_USE_ASYNCIO", True)
_USE_BLEAK = os.environ.get("OBOE_USE_BLEAK", _USE_ASYNCIO)

class _ThreadingBasics: # class to implement some dummy objects like a Lock, so SyncEventDevices can use Locks without boilerplate "if lock: lock.acquire()" statements
  class Lock:           # NOTE: all classes using threading should also work without threading; Locks should only be used to protect sensitive values from race conditions, and not to synchronize code
    def acquire(self, *args, **kwargs) -> bool: return True
    def release(self): pass
    def locked(self) -> bool: return False
    def __enter__(self) -> bool: return True
    def __exit__(self, *args, **kwargs): pass
    
threading = _ThreadingBasics
eventloop = None
if _USE_THREADING:
  try:
    import threading
    from . import eventloop
  except ImportError:
    _USE_THREADING = False
    
asyncio = None
if _USE_ASYNCIO:
  try:
    import asyncio
  except ImportError:
    _USE_ASYNCIO = False
    
bleak = None
if _USE_BLEAK:
  try:
    import bleak
  except ImportError:
    _USE_BLEAK = False