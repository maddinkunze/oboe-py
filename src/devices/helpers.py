import enum

class NestedEnum(enum.Enum):
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
            if isinstance(nested, enum.EnumMeta):
                for enm in nested:
                    self.__setattr__(enm.name, enm)
                    
                    
def _bytesToBitmask(bytes):
  ret = 0
  for b in bytes:
    ret <<= 8
    ret |= b
  return ret
  
def _bytesToMacAddress(bytes):
  return ":".join([f"{p:02x}" for p in bytes])

def _bytesToHexString(bytes):
  return " ".join([f"{p:02x}" for p in bytes])

def _macAddressToBytes(macAddress):
  return bytes(map(lambda x: int(x, 16), (macAddress.split(":"))))

def _applyBitmask(enum, bitmask):
  if (isinstance(bitmask, bytes)):
    bitmask = _bytesToBitmask(bitmask)
  
  return [item for item in enum if bitmask & (1 << item.value)]