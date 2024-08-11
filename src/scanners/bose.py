from devices import bose
from devices.helpers import _bytesToMacAddress

class ScannedBoseDevice:
  def __init__(self, name, macAddress, bmapVersion, isInPairingMode, isDevice1Connected, device1MacAddress, isDevice2Connected, device2MacAddress, productType, productId, productVariant, supportsMusicShare, isInMusicShare):
    self.name = name
    self.macAddress = macAddress
    self.bmapVersion = bmapVersion
    self.isInPairingMode = isInPairingMode
    self.isDevice1Connected = isDevice1Connected
    self.isDevice2Connected = isDevice2Connected
    self.device1Mac = device1MacAddress
    self.device2Mac = device2MacAddress
    self.productType = productType
    self.productId = productId
    self.productVariant = productVariant
    self.supportsMusicShare = supportsMusicShare
    self.isInMusicShare = isInMusicShare
  def __repr__(self):
    return f"ScannedBoseDevice<name={self.name}, macAddress={self.macAddress}, isInPairingMode={self.isInPairingMode}>"


class BoseParser:
  @classmethod
  def _getManufacturerSpecificField(cls, advertisement_data):
    mfd = advertisement_data.manufacturer_data
    if not mfd:
      return None
    
    if len(mfd) != 1:
      return None
    
    for key, data in mfd.items():
      ms1 = key & 0xff
      ms2 = (key >> 8) & 0xff
      return bytearray([ms1, ms2, *data])
    
  @classmethod
  def _isShortenedName(cls, advertisement_data):
    try:
      hasShortName = bool(advertisement_data.platform_data[1].scan.advertisement.get_sections_by_type(0x08).size)
      hasLongName = bool(advertisement_data.platform_data[1].scan.advertisement.get_sections_by_type(0x09).size)
      return hasShortName and not hasLongName # Windows
    except:
      pass
    
    try:
      hasShortName = advertisement_data.platform_data[1].get("AdvertisingData").has(0x08)
      hasLongName = advertisement_data.platform_data[1].get("AdvertisingData").has(0x09)
      return hasShortName and not hasLongName # Linux
    except:
      pass
    
    return False
  
  @classmethod
  def getFullName(cls, device, advertisement_data):
    name = device.name
    if not name:
      name = advertisement_data.local_name
    if not name:
      return None
    
    if name.startswith("LE-"):
      name = name[3:]
      
    if cls._isShortenedName(advertisement_data):
      name += "…"
      
    return name
  
  @classmethod
  def parse(cls, device, advertisement_data):
    mfs_data = cls._getManufacturerSpecificField(advertisement_data)
    if mfs_data is None:
      return
    
    name = cls.getFullName(device, advertisement_data)
    if name is None:
      return

    macAddress = device.address
    
    parserMode = mfs_data[0]
    parser = None
    if parserMode == 0x9E:
      parser = BoseMFSParser120(mfs_data)
    elif parserMode in [0x00, 0x10]:
      parser = BoseMFSParserLegacy(mfs_data)
    elif parserMode == 0x01:
      parser = BoseMFSParser104(mfs_data)
      
    if (not parser) or (not parser.isValid):
      return
        
    return ScannedBoseDevice(name, macAddress, parser.bmapVersion, parser.isInPairingMode, parser.isDevice1Connected, parser.device1MacAddress, parser.isDevice2Connected, parser.device2MacAddress, parser.productType, parser.productId, parser.variantId, parser.supportsMusicShare, parser.isInMusicShare)
  
  
class BoseMFSParser:
  @staticmethod
  def isBitSet(value: int, bitPos: int) -> bool:
    return bool((value >> bitPos) & 0b01)
  
  @staticmethod
  def shiftBitsMagic(value: int, shift1: int, shift2: int) -> int:
    return (value >> shift1) & (255 >> (8 - shift2))

class BoseMFSParserLegacy(BoseMFSParser):
  LENGTH_MINIMUM = 6
  LENGTH_PER_MAC = 6
  def __init__(self, data: bytes):
    self.isValid = True
    
    if len(data) < self.LENGTH_MINIMUM:
      self.isValid = False
      return
    
    bmv1 = self.shiftBitsMagic(data[0], 4, 4)
    bmv2 = self.shiftBitsMagic(data[0], 0, 4) << 4 + self.shiftBitsMagic(data[1], 4, 4)
    bmv3 = self.shiftBitsMagic(data[1], 0, 4)
    self.bmapVersion = f"{bmv1}.{bmv2}.{bmv3}"
    
    self.isInPairingMode = self.isBitSet(data[5], 7)
    
    self.isDevice1Connected = self.isBitSet(data[5], 0)
    self.isDevice2Connected = self.isBitSet(data[5], 1)
    
    expectedLength = self.LENGTH_MINIMUM
    if self.isDevice1Connected:
      expectedLength += self.LENGTH_PER_MAC
    if self.isDevice2Connected:
      expectedLength += self.LENGTH_PER_MAC
    if len(data) != expectedLength:
      self.isValid = False
      return
    
    self.device1MacAddress = None
    self.device2MacAddress = None
    macPos = 6
    if self.isDevice1Connected:
      self.device1MacAddress = _bytesToMacAddress(data[macPos:macPos+6])
      macPos += 6
    if self.isDevice2Connected:
      self.device2MacAddress = _bytesToMacAddress(data[macPos:macPos+6])
    
    self.productId = (data[2] << 8) | data[3]
    self.variantId = data[4]
    
    self.supportsMusicShare = self.isBitSet(data[5], 4) # TODO: also apparently it does not support music sharing, when bmap < 1.0.2
    self.isInMusicShare = self.isBitSet(data[5], 2) or self.isBitSet(data[5], 3)
    
    self.productType = None
    if self.isBitSet(data[5], 5):
      self.productType = bose.BoseDevice.PairedDevice.ProductType.HEADPHONES
    else:
      self.productType = bose.BoseDevice.PairedDevice.ProductType.SPEAKER

class BoseMFSParser104(BoseMFSParser):
  LENGTH_MINIMUM = 9
  LENGTH_PER_MAC = 3
  def __init__(self, data: bytes):
    self.isValid = True
    if len(data) < self.LENGTH_MINIMUM:
      self.isValid = False
      return
    
    if data[0] not in [0x00, 0x01]:
      self.isValid = False
      return
    
    self.bmapVersion = "1.0.4"
    
    self.isDevice1Connected = self.isBitSet(data[2], 4)
    self.isDevice2Connected = self.isBitSet(data[2], 5)
    
    expectedLength = self.LENGTH_MINIMUM
    if self.isDevice1Connected:
      expectedLength += self.LENGTH_PER_MAC
    if self.isDevice2Connected:
      expectedLength += self.LENGTH_PER_MAC
    if len(data) != expectedLength:
      self.isValid = False
      return
    
    self.device1MacAddress = None
    self.device2MacAddress = None
    macPos = 9
    if self.isDevice1Connected:
      self.device1MacAddress = _bytesToMacAddress(bytes(3*b"\x00"+data[macPos:macPos+3]))
      macPos += self.LENGTH_PER_MAC
    if self.isDevice2Connected:
      self.device2MacAddress = _bytesToMacAddress(bytes(3*b"\x00"+data[macPos:macPos+3]))
    
    self.isInPairingMode = self.isBitSet(data[2], 7)
    
    self.productType = None
    if self.isBitSet(data[3], 2):
      self.productType = bose.BoseDevice.PairedDevice.ProductType.HEADPHONES
    else:
      self.productType = bose.BoseDevice.PairedDevice.ProductType.SPEAKER
    
    bleProductId = data[1]
    self.productId = bleProductId # TODO: some magic to convert to actual product id
    self.variantId = self.shiftBitsMagic(data[2], 0, 4)
    
    self.isInMusicShare = self.isBitSet(data[3], 0)
    self.supportsMusicShare = self.isBitSet(data[3], 1)

class BoseMFSParser120(BoseMFSParser):
  def __init__(self, data: bytes): # TODO
    pass
