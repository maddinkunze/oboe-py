import typing
from .types import Operator, Function, FunctionBlock, FunctionBlockEnum, BmapPacket
from .types import BoseProduct, BoseProductId, DeviceName
from .helpers import unknownResponse
from ...basetypes import VersionMajorMinorPatch as VersionMMP, MacAddress, SerialNumber
from ...helpers import Bitmask, bytesToNumber

class FunctionGet(Function):
  @classmethod
  def createGetPacket(cls) -> BmapPacket:
    return cls._createPacket()

class VersionParser(FunctionGet):
  @classmethod
  def parsePacket(cls, packet: BmapPacket) -> VersionMMP:
    super().parsePacket(packet)
    return VersionMMP.fromString(packet.payload.decode())
  
class FunctionBlockInfoParser(VersionParser):
  BYTE = 0x00
  
class MacAddressParser(FunctionGet):
  @classmethod
  def parsePacket(cls, packet: BmapPacket) -> MacAddress:
    super().parsePacket(packet)
    return MacAddress.fromBytes(packet.payload[0:6])
  
class UnknownResponseParser(FunctionGet):
  @classmethod
  @unknownResponse
  def parsePacket(cls, packet: BmapPacket) -> bytes:
    super().parsePacket(packet)
    return packet.payload
  
class TODOParser(Function):
  TODO = True
  @classmethod
  def createGetPacket(cls) -> BmapPacket:
    raise NotImplementedError("TODO")
  @classmethod
  def parsePacket(cls, packet: BmapPacket):
    raise NotImplementedError
  

#################################
#  Function Blocks (Enum-like)  #
#################################

class FunctionBlocks(FunctionBlockEnum):
  class ProductInfo(FunctionBlock):
    BYTE = 0x00
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    class BmapVersion(VersionParser):
      BYTE = 0x01
      
    class AllFunctionBlocks(TODOParser):
      BYTE = 0x02
      
    class ProductIdVariant(FunctionGet):
      BYTE = 0x03
      @classmethod
      def parsePacket(cls, packet: BmapPacket) -> BoseProductId:
        super().parsePacket(packet)
        data = packet.payload
        productId = bytesToNumber(data[0:2])
        variantId = data[2]
        return BoseProduct._getBestFitByBytes(productId, variantId)
      
    class AllFunctions(TODOParser):
      BYTE = 0x04
      
    class FirmwareVersion(VersionParser):
      BYTE = 0x05
      
    class MacAddress(MacAddressParser):
      BYTE = 0x06
      
    class SerialNumber(FunctionGet):
      BYTE = 0x07
      @classmethod
      def parsePacket(cls, packet: BmapPacket) -> SerialNumber:
        super().parsePacket(packet)
        return SerialNumber(packet.payload.decode())
      
    class HardwareRevision(UnknownResponseParser):
      BYTE = 0x0a
      
    class ComponentDevices(UnknownResponseParser):
      BYTE = 0x0b
      
    
  class Settings(FunctionBlock):
    BYTE = 0x01
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    class AllSettings(TODOParser):
      BYTE = 0x01
      
    class DeviceName(FunctionGet):
      BYTE = 0x02
      _MASK_IS_DEFAULT_NAME = Bitmask(0b01)
      @classmethod
      def createSetAndGetPacket(cls, name: str) -> BmapPacket:
        return cls._createPacket(Operator.SET_GET, name.encode())
      @classmethod
      def parsePacket(cls, packet: BmapPacket) -> DeviceName:
        super().parsePacket(packet)
        flags, *name = packet.payload
        isDefaultName = cls._MASK_IS_DEFAULT_NAME.isSet(flags)
        name = bytes(name).decode()
        return DeviceName(name, isDefaultName)
    
    
  class Status(FunctionBlock):
    BYTE = 0x02
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    
  class FirmwareUpdate(FunctionBlock):
    BYTE = 0x03
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    
  class DeviceManagement(FunctionBlock):
    BYTE = 0x04
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    
  class AudioManagement(FunctionBlock):
    BYTE = 0x05
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
  
  
  class Control(FunctionBlock):
    BYTE = 0x07
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
  
  
  class Notifications(FunctionBlock):
    BYTE = 0x09
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
  
  
  class HearingAssistance(FunctionBlock):
    BYTE = 0x0c
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass

    
  class DataCollection(FunctionBlock):
    BYTE = 0x0d
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
    
    
  class HeartRate(FunctionBlock):
    BYTE = 0x0e
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
  
  
  class VoicePersonalAssistant(FunctionBlock):
    BYTE = 0x10
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass
  
  
  class AugmentedReality(FunctionBlock):
    BYTE = 0x15
    
    class FunctionBlockInfo(FunctionBlockInfoParser): pass