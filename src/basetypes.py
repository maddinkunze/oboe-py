import abc
import typing

class Version(abc.ABC):
  pass

class VersionMajorMinorPatch(Version):
  def __init__(self, major, minor, patch):
    self.major = major
    self.minor = minor
    self.patch = patch
    
  def __str__(self):
    return f"{self.major}.{self.minor}.{self.patch}"
  
  def __repr__(self):
    return f"Version<major={self.major}, minor={self.minor}, patch={self.patch}>"
  
  @classmethod
  def fromString(cls, string: str) -> typing.Self:
    major, minor, patch = map(int, string.split(".", 2))
    return cls(major, minor, patch)


class ProductId:
  def getSimpleName(self) -> str:
    raise NotImplementedError
  def getFullName(self) -> str:
    raise NotImplementedError
  def __str__(self) -> str:
    return self.getFullName()
  def __repr__(self) -> str:
    return f"ProductId<name={self.getFullName()}>"


class SerialNumber:
  def __init__(self, serialNo):
    self.serialNo = serialNo
    
  def __str__(self) -> str:
    return self.serialNo
  
  def __repr__(self) -> str:
    return f"SerialNumber<serialNo={self.serialNo}>"


class DeviceAddress:
  def __init__(self, address):
    self.address = address
    
  def __str__(self) -> str:
    return self.address
  
  def __repr__(self):
    return f"DeviceAddress<address={str(self)}>"

class MacAddress(DeviceAddress):
  def __init__(self, o1, o2, o3, o4, o5, o6):
    self.o1 = o1
    self.o2 = o2
    self.o3 = o3
    self.o4 = o4
    self.o5 = o5
    self.o6 = o6
  
  @property
  def address(self):
    return str(self)
  
  @classmethod
  def fromString(cls, string: str) -> typing.Self:
    return cls(*string.split(":"))
  
  @classmethod
  def fromBytes(cls, bytes: bytearray) -> typing.Self:
    return cls(*bytes)
    
  def __str__(self) -> str:
    return ":".join(map(lambda x: f"{x:02x}", self.toList()))
  
  def __repr__(self) -> str:
    return f"MacAddress<address={str(self)}>"
  
  def toList(self) -> list[int]:
    return [self.o1, self.o2, self.o3, self.o4, self.o5, self.o6]
  
  def toBytes(self) -> bytes:
    return bytes(self.toList())
  
  
class OboeException(Exception):
  pass

class PeripheralException(OboeException):
  pass