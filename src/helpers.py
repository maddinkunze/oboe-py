import time
import typing
from . import libraries
from enum import Enum, EnumMeta
from typing import Callable

class NestedEnum(Enum):
    def __new__(cls, *args):
        obj = object.__new__(cls)
        value = None
        # Normal Enumerator definition
        if len(args) == 1:
            value = args[0]

        # Have a tuple of values, first de value and next the nested enum (I will set in __init__ method)
        if len(args) == 2:
            value = args[0]

        if value:
            obj._value_ = value

        return obj

    def __init__(self, name, nested=None):
        # At this point you can set any attribute what you want
        if nested:
            # Check if is an Enumerator you can comment this if you want another object
            if isinstance(nested, EnumMeta):
                for enm in nested:
                    self.__setattr__(enm.name, enm)
                    
def EnumWithData(**data) -> type[Enum]:
  class _EnumWithData(Enum):
    def __init__(self, *args, **kwargs):
      super().__init__(self, *args, **kwargs)
      for key, value in data.items():
        setattr(self, key, value)
    
  return _EnumWithData

class CachedValue[T]:
  class _Sentinel(object): pass
  _SENTINEL = _Sentinel()
  
  def __init__(self, functionToRefresh: Callable[[], None], *, initialValue: T|_Sentinel = _SENTINEL, invalidateAfter: int|float|None = None, invalidValue: T|_Sentinel = _SENTINEL, shouldUpdateImmediately: bool = False, shouldUpdateOnFirstUse: bool = True):
    self._value = function() if shouldUpdateImmediately else initialValue
    self.invalidateAfter = invalidateAfter
    self.functionToRefresh = functionToRefresh
    self._invalidValue = invalidValue
    self._nextUpdate: float|None = 0 if shouldUpdateOnFirstUse else None
    
  @property
  def value(self) -> T:
    return self.getValue()
  
  def getValue(self, *, updateIfOutdated: bool = True) -> T:
    if self.shouldUpdate(updateIfOutdated=updateIfOutdated):
      self.functionToRefresh()
      
    return self._value
  
  @value.setter
  def value(self, value: T):
    self.setValue(value)
    
  def setValue(self, value: T, *, countAsUpdate: bool = True):
    self._value = value
    if not countAsUpdate:
      return
    self._nextUpdate = None if self.invalidateAfter is None else time.time() + self.invalidateAfter
  
  @property
  def isInvalid(self):
    return self._value is self._invalidValue
  
  @property
  def isOutdated(self):
    if self._nextUpdate is None:
      return False
    
    if (self._nextUpdate is not None) and (time.time() >= self._nextUpdate):
      return True
    
    return False
  
  def shouldUpdate(self, *, updateIfOutdated: bool = True):
    if self.isInvalid:
      return True
    if updateIfOutdated and self.isOutdated:
      return True
    return False
  
  def scheduleUpdate(self, after: int|float|None = None, force: bool = False):
    nextUpdate = 0 if after is None else time.time() + after
    if (not force) and (nextUpdate > self._nextUpdate):
      return
    self._nextUpdate = nextUpdate
  
  def invalidate(self):
    self._value = self._invalidValue
    self.scheduleUpdate()

class ValueCollection[K, V]:
  def __init__(self):
    self._data0 = dict[K, V]()
    self._data1 = dict[K, V]()
    self._pointerRead = 0
    self._isCollecting = False
    self._initLocks()
    
  def _initLocks(self):
    self._lock = libraries.threading.Lock()
  
  # starts collecting
  def startCollecting(self):
    with self._lock:
      self._startCollecting()
  
  def _startCollecting(self):
    self._isCollecting = True
  
  def stopCollectingAndMarkReadable(self):
    with self._lock:
      self._stopCollecting()
  
  def _stopCollecting(self):
    if not self._isCollecting:
      return
    self._isCollecting = False
    self._pointerRead = self._getBufferNum(1)
  
  def _getBufferNum(self, reading0Writing1: int=0) -> int:
    return (self._pointerRead + reading0Writing1) % 2
  
  def _getBuffer(self, reading0Writing1: int=0) -> dict[K, V]:
    if self._getBufferNum(reading0Writing1):
      return self._data1
    else:
      return self._data0
  
  def write(self, key: K, value: V):
    with self._lock:
      self._write()
   
  def _write(self, key: K, value: V):
    if not self._isCollecting:
      return
    self._getBuffer(1)[key] = value
  
  def read(self, key: K, default: V|None=None) -> V|None:
    with self._lock:
      self._read(key, default)
  
  def _read(self, key: K, default: V|None=None) -> V|None:
    return self._getBuffer().get(key, default)
  
  def copy(self) -> dict[K, V]:
    with self._lock():
      return self._copy()
    
  def _copy(self) -> dict[K, V]:
    return self._getBuffer().copy()

  
class classproperty:
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

def bytesToHexString(data: bytes):
  return " ".join([f"{p:02x}" for p in data])

def applyBitmask(enum: Enum, bitmask: int, attr: str|None=None):
  if isinstance(bitmask, bytes) or isinstance(bitmask, list) or isinstance(bitmask, tuple):
    bitmask = bytesToNumber(bitmask)
  
  def _isBitSet(item: Enum):
    if attr:
      value = getattr(item, attr)
    else:
      value = item.value
    if value < 0:
      return False
    return bitmask & (1 << value)
  
  return [item for item in enum if _isBitSet(item)]

def bytesToNumber(data: list[int]|bytes, firstIsLowest: bool=False) -> int:
  ret = 0
  if firstIsLowest:
    data = reversed(data)
  for e in data:
    ret <<= 8
    ret |= (e & 255)
  return ret

# masks the value according to the bitmask and pushes it to the front, e.g.:
# valueInBitmask : 01101110
# bitmask        : 00111100
#                  --------
#                  00101100 (mask value by ANDing valueInBitmask and bitmask)
#                  ..1011.. (<- this is the value we would like to have, but we first need to shift it 2 to the left. the 2 comes from the number of zeroes on the right side of the bitmask, in this example 00111100 -> ......00 -> 2)
#                      1011 (<- final value)

class Bitmask:
  def __init__(self, mask: int):
    self.mask = mask
    self._sPos, self._sLen = self._getShiftPosAndLength(mask)
    
  @staticmethod
  def _getShiftPosAndLength(mask: int) -> tuple[int, int]|tuple[None, None]:
    # find position and length of single continuous block of 1s
    # e.g.: 0b00110000 -> pos = 4, length = 2 -> (4, 2)
    #       0b01111000 -> pos = 3, length = 4 -> (3, 4)
    #       0b01001100 -> invalid, because there are two separate blocks
    pos = None
    length = None
    i = 0
    while mask:
      if (mask & 0b01):
        if pos is None:
          pos = i
          length = 0
        length += 1
      elif pos is not None:
        pos = None
        length = None
        break
      
      mask >>= 1
      i += 1
    return pos, length
    
  @classmethod
  def fromPositions(cls, pos1: int, pos2: int) -> typing.Self:
    pos = min(pos1, pos2)
    length = abs(pos2 - pos1) + 1
    return cls.fromPositionAndLength(pos, length)
  
  @classmethod
  def fromPositionAndLength(cls, pos: int, length: int) -> typing.Self:
    mask = ((1 << length) - 1) << pos  # e.g.: pos=3, length=5 -> [1 << length -> 0b100000] -> [0b100000 - 1 -> 0b11111] -> [0b11111 << pos -> 0b11111000]
    return cls(mask)
  
  def _sPosOrRaise(self) -> int:
    sPos = self._sPos
    if sPos is None:
      raise ValueError(f"The provided bitmask ({self.mask:b}) does not contain one single continuous block of 1s")
    return sPos
  
  def shift(self, value: int) -> int:
    # e.g.: mask=0b01111000, value=11 -> [mask=0b01111000 -> _sPos=3] -> [11 -> 0b1011] -> [0b1011 << 3(=_sPos) -> 0b1011000] -> 0b01011000, also see unshift()
    return self.apply(value << self._sPosOrRaise())
  
  def unshift(self, value: int) -> int:
    # e.g.: mask=0b01111000, value=0b11011001 -> [mask=0b01111000 -> _sPos=3] -> [value & mask -> 0b11011001 & 0b01111000 -> 0b01011000] -> [0b01011000 >> _sPos -> 0b01011000 >> 3 -> 0b00001011] -> 0b1011 -> 11, also see shift()
    return self.apply(value) >> self._sPosOrRaise()
  
  def apply(self, value: int) -> int:
    return value & self.mask
  
  def isSet(self, value: int) -> bool:
    if self._sLen != 1:
      raise ValueError(f"The provided bitmask ({self.mask:b}) does not contain a single 1")
    return bool(self.apply(value))
  

def TODO(msg="Not yet implemented, if you think your device supports this function please fill in this functionality and create a pull request"):
  raise NotImplementedError(msg)