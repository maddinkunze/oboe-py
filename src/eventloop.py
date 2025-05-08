import time
import typing
import threading

_w_lock: threading.Lock = threading.Lock()
_thread: threading.Thread|None = None
_callbacks: list[typing.Callable] = []
_callbacks_weakref: None = None
_TIME_STEP = 0.001

weakref = None
try:
  import weakref, weakref as wr
  _callbacks_weakref: list[wr.ReferenceType[typing.Callable]] = []
except ImportError:
  pass
  

def addCallback(cb: typing.Callable, *, as_weakref: bool=True):
  with _w_lock:
    _addCallback(cb, as_weakref=as_weakref)
  
def _addCallback(cb: typing.Callable, *, as_weakref: bool=True):
  _removeCallback(cb)
  if weakref and as_weakref:
    _callbacks_weakref.append(weakref.ref(cb))
  else:
    _callbacks.append(cb)
  _startWorkerThreadIfNecessary()

def removeCallback(cb: typing.Callable):
  with _w_lock:
    _removeCallback(cb)

def _removeCallback(cb: typing.Callable):
  try:
    _callbacks.remove(cb)
  except ValueError:
    pass
  
  if not _callbacks_weakref:
    return
  for wr in _callbacks_weakref:
    if wr() != cb:
      continue
    _removeWRCallback(wr)

def _removeWRCallback(ref):
  if not ref:
    return
  try:
    _callbacks_weakref.remove(ref)
  except ValueError:
    pass

def startWorkerThreadIfNecessary():
  with _w_lock:
    _startWorkerThreadIfNecessary
  
def _startWorkerThreadIfNecessary():
  global _thread
  if _thread:
    return
  _thread = threading.Thread(target=_workerLoop, daemon=True)
  _thread.start()

def _getAllCallbacks():
  cbs = _callbacks.copy()
  for ref in _callbacks_weakref:
    cb = ref()
    if cb is None:
      _removeWRCallback(ref)
      continue
    cbs.append(cb)
  return cbs

def _workerLoop():
  global _thread
  while True:
    with _w_lock:
      cbs = _getAllCallbacks()
      if not cbs:
        _thread = None
        return
      
    for cb in cbs:
      try:
        cb()
      except:
        pass
      
    del cbs  # -> clear up any references that should only be accessible via weakref (by calling _getAllCallbacks() we create a reference to the previously only weakref-ed callbacks, preventing them from being garbage-collected. by removing those references and waiting for a short time (time.sleep(_TIME_STEP)), we allow those references to be garbage-collected, if this is the only thread holding a reference)
    
    time.sleep(_TIME_STEP)