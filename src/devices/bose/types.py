import typing
from enum import Enum, IntFlag
#from .errors import getErrorMessageFromBytes # TODO: circular import, not good
from ...helpers import classproperty, applyBitmask, Bitmask, bytesToHexString
from ... import basetypes as bt

class Operator(Enum):
  SET     = 0
  GET     = 1
  SET_GET = 2
  STATUS  = 3
  ERROR   = 4
  START   = 5
  FINAL   = 6
  PROCESS = 7
  
  def __init__(self, value):
    self.BYTE = value
  
  def isError(self):
    return self == self.__class__.ERROR
OperatorT: typing.TypeAlias = Operator

# the following classes without leading underscore (_XXX) are primarily for type checking, function-stubs and autocompletion
# the following classes with leading underscore (_XXX) are used for implementing a typed bidirectional "tree" (i.e. all parents know their children and the children know their parent):
# | FunctionBlockEnum:                                 <- knows all its "enum" items (function blocks), has a map of all items and their corresponding BYTE-value (can be resolved at runtime using getFunctionBlockByByte())
# |  - ProductInfo     (FB_BYTE=0x00)                  <- knows all its "enum" items (functions), has a map of all items and their corresponding BYTE-value (can be resolved at runtime using getFunctionByByte()); does not need to know its parent
# |     - FBlockInfo   (F_BYTE=0x00, FB=ProductInfo)   <- knows its parent (i.e. ProductInfo), so it can build packets on its own
# |     - MacAddress   (F_BYTE=0x06, FB=ProductInfo)
# |     - SerialNumber (F_BYTE=0x07, FB=ProductInfo)
# |     - ...
# |  - Settings        (FB_BYTE=0x01)
# |     - FBlockInfo   (F_BYTE=0x00, FB=Settings)   <- knows its parent (i.e. Settings)
# |     - DeviceName   (F_BYTE=0x02, FB=Settings)   <- knows its parent (i.e. Settings)
# |     - StandbyTimer (F_BYTE=0x03, FB=Settings)
# |     - ...
# |  - ...
class Function:
  BYTE: int
  FUNCTION_BLOCK: typing.Type["FunctionBlock"] # will automatically be filled in by the FunctionsBase metaclass
    
  @classmethod
  def _createPacket(cls, operator: Operator=Operator.GET, payload: bytes|None=None) -> "BmapPacket":
    return BmapPacket(cls, operator, payload)
  
  @classmethod
  def parsePacket(cls, packet: "BmapPacket"):
    raise NotImplementedError
FunctionT: typing.TypeAlias = typing.Type[Function]

class _FunctionsBase(type):
  def __new__(metacls, cls, bases, classdict: dict[str, typing.Any], *_, **__):
    mapping = dict[int, FunctionT]()
    for item in classdict.values():
      if not isinstance(item, type):
        continue
      if not issubclass(item, Function):
        continue
      mapping[item.BYTE] = item
      item.FUNCTION_BLOCK = cls
    if mapping:
      classdict["getByByte"] = lambda byte: mapping[byte]
    t: FunctionBlock = super().__new__(metacls, cls, bases, classdict, *_, **__)
    t.getFunctionByByte = lambda byte: mapping[byte]
    return t

class FunctionBlock(metaclass=_FunctionsBase):
  BYTE: int
  
  @staticmethod
  def getFunctionByByte(byte: int) -> Function: # only for type-checking, the actual implementation is within the _FunctionsBase.__new__() method
    pass
  
class _FunctionBlocksBase(type):
  def __new__(metacls, cls, bases, classdict: dict[str, typing.Any], *_, **__):
    mapping = dict[int, FBlockT]()
    for item in classdict.values():
      if not isinstance(item, type):
        continue
      if not issubclass(item, FunctionBlock):
        continue
      mapping[item.BYTE] = item
    t: FunctionBlockEnum = super().__new__(metacls, cls, bases, classdict, *_, **__)
    t.getBlockByByte = lambda byte: mapping[byte]
    return t
FBlockT: typing.TypeAlias = typing.Type[FunctionBlock]
  
class FunctionBlockEnum(metaclass=_FunctionBlocksBase):
  @staticmethod
  def getBlockByByte(byte: int) -> FunctionBlock: # only for type-checking, the actual implementation is within the _FunctionBlocksBase.__new__() method
    pass
  
  @classmethod
  def getFunctionByBytes(cls, functionBlockByte: int, functionByte: int) -> Function:
    return cls.getBlockByByte(functionBlockByte).getFunctionByByte(functionByte)


class BmapPacket:
  _MASK_OPERATOR = Bitmask(0b00001111)
  _MASK_DEVICEID = Bitmask(0b00110000)
  _MASK_PORT     = Bitmask(0b11000000)
  _DEFAULT_DEVID = 0
  _DEFAULT_PORT = 0
  _SIZE_HEADER = 4
  
  def __init__(self, function: FunctionT, operator: Operator, payload: bytes, deviceId: int=_DEFAULT_DEVID, port: int=_DEFAULT_PORT):
    self.function = function
    self.operator = operator
    self.deviceId = deviceId
    self.port = port
    self.payload = payload
    
  @property
  def header(self) -> bytes:
    b1 = self.function.FUNCTION_BLOCK.BYTE
    b2 = self.function.BYTE
    b3 = self._MASK_OPERATOR.shift(self.operator.BYTE) \
       | self._MASK_DEVICEID.shift(self.deviceId) \
       | self._MASK_PORT.shift(self.port)
    b4 = len(self.payload)
    return bytearray([b1, b2, b3, b4])
    
  def toBytes(self) -> bytes:
    return bytearray([*self.header, *self.payload])
  
  @classmethod
  def _headerFromBytes(cls, data: bytes) -> tuple[int, int, int, int, bytes, bytes]|None:
    if len(data) < cls._SIZE_HEADER:
      return None

    functionBlockByte, functionByte, odpByte, lengthByte, *payloadBytes = data
    payloadBytes, remainingBytes = payloadBytes[:lengthByte], payloadBytes[lengthByte:]
    return functionBlockByte, functionByte, odpByte, lengthByte, payloadBytes, remainingBytes
  
  @classmethod
  def fromBytes(cls, data: bytes) -> typing.Self|None:
    header = cls._headerFromBytes(data)
    if not header:
      return None
    
    functionBlockByte, functionByte, odpByte, lengthByte, payloadBytes, remainingBytes = header
    if remainingBytes:
      return None
    
    return cls._fromSplitBytes(functionBlockByte, functionByte, odpByte, payloadBytes)
    
  @classmethod
  def splitFromBytes(cls, data: bytes) -> tuple[typing.Self|None, bytes]:
    header = cls._headerFromBytes(data)
    if not header:
      return None, data
    
    functionBlockByte, functionByte, odpByte, lengthByte, payloadBytes, remainingBytes = header
    return cls._fromSplitBytes(functionBlockByte, functionByte, odpByte, payloadBytes), remainingBytes
  
  @classmethod
  def splitFromBytesMulti(cls, data: bytes) -> tuple[list[typing.Self], bytes]:
    packets = []
    remaining = data
    while True:
      packet, remaining = cls.splitFromBytes(remaining)
      if not packet:
        break
      packets.append(packet)
    return packets, remaining
    
  @classmethod
  def _fromSplitBytes(cls, functionBlockByte: int, functionByte: int, odpByte: int, payloadBytes: bytes) -> typing.Self:
    function = FunctionBlockEnum.getFunctionByBytes(functionBlockByte, functionByte)
    operator = Operator(cls._MASK_OPERATOR.unshift(odpByte))
    deviceId = cls._MASK_DEVICEID.unshift(odpByte)
    port = cls._MASK_PORT.unshift(odpByte)
    return cls(function, operator, payloadBytes, deviceId, port)
  
  def __repr__(self):
    return f"BmapPacket<function={self.function}, operator={self.operator}, payload=[{bytesToHexString(self.payload)}], (deviceId={self.deviceId}, port={self.port})>"
    

class BoseProductId(bt.ProductId):
  def __init__(self):
    self.product: BoseProduct
    self.variant: BoseVariant|None = None
  def getProductName(self):
    return self.product.productName
  def getVariantName(self):
    variant = self.variant
    if not variant:
      return None
    return variant.variantName
  def getSimpleName(self) -> str:
    return self.getProductName()
  def getFullName(self) -> str:
    productName = self.getProductName()
    variantName = self.getVariantName()
    if not variantName:
      return productName
    return f"{productName} ({variantName})"
  def __repr__(self):
    return f"BoseProductId<product={self.getProductName()}, variant={self.getVariantName()}>"

class BoseVariant(BoseProductId, Enum):
  def __init__(self, *args, **kwargs):
    if len(args) == 1:
      args = args[0]
    self._init(*args)
      
  def _init(self, product: BoseProductId, variantName: str, variantId: int):
    self.product = product
    self.variant = self
    
    self.variantName = variantName
    self.variantId = variantId
  
class SupportedProfiles(IntFlag):
  SPP = 0
  A2DP = 1
  HEART_RATE = 4
  @classproperty
  def DEFAULT(cls):
    return cls.A2DP

class _HWRevParser:
  @staticmethod
  def DEFAULT(hwrev: str) -> str:
    return "*"
  
  @staticmethod
  def STETSON(hwrev: str) -> str|None:
    lower = hwrev.strip().lower()
    if not lower:
      return None
    if ("dp0" in lower) or ("qs1" in lower):
      return "00.10.00"
    length = len(lower)
    if not (16 <= length <= 17):
      return None
    length -= 10
    try:
      if int(lower[length]) != 6:
        return None
      version = int(lower[length+1:length+4])
      if 117 <= version <= 120:
        return "00.30.00"
      if not (220 <= version <= 243):
        return None
      return "01.00.00"
    except:
      return None

class BoseProduct(BoseProductId, Enum):      
  def __init__(self, *args):
    if len(args) == 1:
      args = args[0]
    self._init(*args)

  def _init(self, btId: int, bleId: int, productName: str, supportedProfiles: SupportedProfiles, hwRevParser: typing.Callable, variants: None|typing.Type[BoseVariant]|list|tuple|None):
    self.product = self

    self.btId = btId
    self.bleId = bleId
    self.productName = productName
    self.supportedProfiles = supportedProfiles
    self._hwRevParser = hwRevParser
    if (variants is not None) and (not isinstance(variants, BoseVariant)):
      variants = [(variant[0].upper().replace(" ", "_"), (self, *variant)) for variant in variants]
      variantsEnumName = "".join(map(str.capitalize, self.name.split("_"))) + "_Variant"
      variants = BoseVariant(variantsEnumName, variants)
    self.variants = variants
    
  @classmethod
  def _getBestFitByBytes(cls, product: int, variant: int, *, useBleId: bool=False) -> BoseProductId:
    ret = cls.UNKNOWN
    for item in cls:
      _id = item.bleId if useBleId else item.btId
      if _id != product:
        continue
      ret = item
      break

    for item in ret.variants or []:
      if item.variantId != variant:
        continue
      ret = item
      break

    return ret

  UNKNOWN              = 0,     -1,  "Unknown Device",                       SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Unknown', 0)]
  UNKNOWN_120          = 0,     100, "Unknown Device",                       SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Unknown', 0)]
  ISAAC                = 16394, 0,   "Bose AE2 SoundLink",                   SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('White', 2)]
  WOLFCASTLE           = 16396, 1,   "Bose QuietComfort 35",                 SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Silver', 2), ('Ornament', 3), ('Greta', 4)]
  ICE                  = 16402, 2,   "Bose SoundSport",                      SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Blue', 2), ('Yellow', 3)]
  FLURRY               = 16403, 3,   "Bose SoundSport Pulse",                SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Red', 1)]
  POWDER               = 16404, 4,   "Bose QuietControl 30",                 SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('White', 2), ('Stark Black', 3), ('Stark White', 4)]
  FOREMAN              = 16397, 5,   "Bose SoundLink Color II",              SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('White', 2), ('Red', 3), ('Blue', 4), ('Midnight Blue', 5), ('Yellow Citron', 6)]
  HARVEY               = 16401, 7,   "Bose Revolve+ Soundlink",              SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('White', 2)]
  FOLGERS              = 16400, 6,   "Bose Revolve Soundlink",               SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('White', 2)]
  KLEOS                = 16407, 8,   "Bose SoundWear",                       SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1)]
  BAYWOLF              = 16416, 9,   "Bose QuietComfort 35 Series 2",        SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Silver', 2), ('Navy', 3), ('Peacock', 4), ('Nymeria', 5)]
  LEVI                 = 16408, 10,  "Bose SoundSport Free",                 SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Citron', 2), ('Orange', 3), ('Purple', 4)]
  LEVI_SLAVE           = 16409, 11,  "Bose SoundSport Free",                 SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  MINNOW               = 16418, 12,  "Bose SoundLink Micro",                 SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Blue', 2), ('Orange', 3), ('Stone Blue', 4), ('White Smoke', 5)]
  ATLAS                = 16417, 13,  "Bose ProFlight",                       SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1)]
  GOODYEAR             = 16420, 15,  "Bose Noise Cancelling Headphones 700", SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('Silver', 2), ('Sheng', 3), ('Fuji', 4), ('Fortera', 6)]
  CHIBI                = 41489, 21,  "Bose S1 Pro",                          SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1)]
  CELINE               = 16428, 22,  "Bose Frames",                          SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Alto', 1), ('Rondo', 2)]
  REVEL                = 16429, 25,  "Bose Sport Earbuds",                   SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('Baltic Blue', 2), ('Glacier White', 3)]
  LANDO                = 16431, 28,  "Bose QuietComfort Earbuds",            SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('Nue Lux', 2), ('Stone Blue', 5), ('Sandstone', 6)]
  CELINE_II            = 16460, 32,  "Bose Frames",                          SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, None
  GWEN                 = 16442, 33,  "Bose Sport Open Earbuds",              SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1)]
  OLIVIA               = 16480, 44,  "Bose Frames Tempo",                    SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Tempo', 1)]
  VEDDER               = 16481, 45,  "Bose Frames",                          SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Soprano', 1), ('Tenor', 2)]
  PHELPS               = 48217, 54,  "Bose SoundLink Flex",                  SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Nue Bose Black', 1), ('Smoke White', 2), ('Stone Blue', 3), ('Carmine Red', 4), ('Cypress Green', 5), ('Chilled Lilac', 6)]
  DURAN                = 16441, 55,  "Bose QuietComfort 45",                 SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Nue Bose Black', 1), ('White Smote', 2), ('Midnighht Blue', 3), ('Eclipse Grey', 4)]
  PHELPS_II            = 48224, 67,  "Bose SoundLink Flex",                  SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, None
  PRINCE               = 16501, 71,  "Bose QuietComfort Headphones",         SupportedProfiles.A2DP,    _HWRevParser.DEFAULT, [('Black', 1), ('White Smoke', 2), ('Midnight Blue', 3), ('Eclipse Grey', 4), ('Cypress Green', 5), ('Moonstone Blue', 6)]
  SMALLS               = 16484, 101, "Bose QC Earbuds II",                   SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('Soapstone', 2), ('Midnight Blue', 3), ('Eclipse Grey', 4)]
  LONESTARR            = 16486, 103, "Bose QC Ultra Headphones",             SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, [('Black', 1), ('White Smoke', 2), ('Sandstone', 3)]
  SCOTTY               = 16498, 104, "Bose QC Ultra Earbuds",                SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  STETSON              = 16405, -1,  "Bose Hearphones",                      SupportedProfiles.DEFAULT, _HWRevParser.STETSON, [('Black', 1)]
  LEVI_CASE            = 16410, -1,  "Levi Case",                            SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  BEANIE               = 16427, -1,  "Bose Hearphones II",                   SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  BUDLITE              = 16436, -1,  "Bose Budlite",                         SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  SMALLS_CASE          = 16485, -1,  "Bose QC Earbuds II Case",              SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None
  SCOTTY_CHARGING_CASE = 16499, -1,  "Bose QC Ultra Earbuds Case",           SupportedProfiles.DEFAULT, _HWRevParser.DEFAULT, None

class DeviceName:
  def __init__(self, name: str, isDefaultName: bool):
    self.name = name
    self.isDefaultName = isDefaultName

class VolumeData:
  def __init__(self, current, maximum):
    self.current = current
    self.maximum = maximum
    
  @property
  def percentage(self):
    return round(100 * (self.current/self.maximum), 2)
  
  def _calculateVolumeForBoseDevice(self, volume):
    maxVolume = self.maximum
    curVolume = round((volume/100) * maxVolume)
    if curVolume < 0:
      return 0
    if curVolume > maxVolume:
      return maxVolume
    return curVolume
  
class VoicePromptSetting:
  class Language(Enum):
    def __init__(self, *args):
      if len(args) == 1:
        args = args[0]
      self._init(*args)
    
    @classproperty
    def _BYTE_ATTR(cls): return "byte"
    
    def _init(self, byte: int, englishName: str, nativeName: str, nativeAndEnglishCombined: bool = False, specifier: str|None = None):
      self.byte = byte
      self.englishName = englishName
      self.nativeName = nativeName
      self._nativeAndEnglishCombined = nativeAndEnglishCombined
      self.specifier = specifier
      
    UNKNOWN = -1, "Unknown",    "Unknown"
    EN_UK = 0x00, "English",    "English", False, "UK"
    EN_US = 0x01, "English",    "English", False, "US"
    FR    = 0x02, "French",     "Français"
    IT    = 0x03, "Italian",    "Italiano"
    DE    = 0x04, "German",     "Deutsch"
    ES_EU = 0x05, "Spanish",    "Español", False, "EU"
    ES_MX = 0x06, "Spanish",    "Español", False, "MX"
    PT    = 0x07, "Portuguese", "Português"
    ZH    = 0x08, "Mandarin",   "普通话", True
    KO    = 0x09, "Korean",     "한국어", True
    RU    = 0x0a, "Russian",    "Русский", True
    PL    = 0x0b, "Polish",     "Polski"
    HE    = 0x0c, "Hebrew",     "עִברִית", True
    TK    = 0x0d, "Turkish",    "Türk"
    NL    = 0x0e, "Dutch",      "Nederlands"
    JA    = 0x0f, "Japanese",   "日本語", True
    CA    = 0x10, "Cantonese",  "廣東話", True
    AR    = 0x11, "Arabic",     "العربية", True
    SV    = 0x12, "Swedish",    "Svensk",
    DA    = 0x13, "Danish",     "Dansk",
    NO    = 0x14, "Norwegian",  "Norsk",
    SK    = 0x15, "Finnish",    "Suomen kieli", True
    
    @classmethod
    def _getByByte(cls, byte: int):
      for l in cls:
        if l.byte == byte:
          return l
      return cls.UNKNOWN
  
  def __init__(self, canChange: bool, isEnabled: bool, language: Language, supportedLanguages: list[Language]):
    self.canChange = canChange
    self.isEnabled = isEnabled
    self.language = language
    self.supportedLanguages = supportedLanguages
    
  def _getPayload(self):
    b = self.language.value & self._LANGUAGE
    if (self.isEnabled):
      b |= self._IS_ENABLED
    return bytes([b])
  
  def __repr__(self):
    return f"VoicePromptSetting<canChange={self.canChange}, isEnabled={self.isEnabled}, language={self.language.name}, supportedLanguages={'|'.join([l.name for l in self.supportedLanguages])}>"
  
class AnrLevel(Enum):
  OFF  = 0x00
  HIGH = 0x01
  WIND = 0x02
  LOW  = 0x03
  
class ActionButtonSetting:
  class ActionButtonModes(Enum):
    NOT_CONFIGURED = 0
    VOICE_PERSONAL_ASSISTANT = 1
    ANR = 2
    BATTERY_LEVEL = 3
    PLAY_PAUSE = 4
    
  _DEFAULT_BUTTON_ID = 16  # idk why
  _DEFAULT_EVENT_TYPE = 4  # idk why
  _DEFAULT_FUNCTION = ActionButtonModes.NOT_CONFIGURED
  _DEFAULT_FUNCTIONS = []
    
  def __init__(self, bytes):
    self.isConfigurable = False
    self.buttonId = self._DEFAULT_BUTTON_ID
    self.buttonEventType = self._DEFAULT_EVENT_TYPE
    self.configuredFunctionality = self._DEFAULT_FUNCTION
    self.supportedFunctionality = self._DEFAULT_FUNCTIONS
    
    if (len(bytes) == 1):  # idk why,  but this seems to be an indicator, that the button is not configurable right now
      return
    
    self.isConfigurable = True
    self.buttonId = bytes[0]
    self.buttonEventType = bytes[1]
    self.configuredFunctionality = self.ActionButtonModes(bytes[2])
    self.supportedFunctionality = applyBitmask(self.ActionButtonModes, bytes[3:])
    
  def _getPayload(self):
    return bytes([self.buttonId, self.buttonEventType, self.configuredFunctionality.value])
    
class SidetoneLevel(Enum):
  OFF    = 0
  HIGH   = 1
  MEDIUM = 2
  LOW    = 3
  
class ProductType(Enum):
  HEADPHONES = 1
  SPEAKER = 2

class PairedDevice:
  def __init__(self, bytes):
    self.macAddress = bt.MacAddress(*bytes[:6])
    self.isConnected   = bool(bytes[6] & 0b0001)
    self.isLocalDevice = bool(bytes[6] & 0x0010)
    self.isBoseProduct = bool(bytes[6] & 0x0100)
    self.productType = None
    self.productId = None
    
    pos = 9 # if it is a normal device, the name starts at pos 9
    if self.isBoseProduct:
      pos = 10 # if it is a bose device, the name starts at pos 10
      self.productType = ProductType((bytes[6] >> 7) & 0b01) # can only ever be headphones apparently, since there is only one bit, but what about the second bit needed to represent speaker = 2 = 0b10?
      self.productId = (bytes[7] << 8) | bytes[8]
      self.productVariant = bytes[9]
    
    self.name = bytes[pos:].decode()
  
class ChirpStopReason(Enum):
  NEVER_SAW_CHIRP = 0
  USER_PUSHED_BUTTON = 1
  TIMED_OUT = 2
  STOPPED = 3
  USER_REMOVED_BUD = 4
  
class AudioControlMode(Enum):
  STOP = 0
  PLAY = 1
  PAUSE = 2
  TRACK_FORWARD = 3
  TRACK_BACK = 4
  FAST_FORWARD_PRESS = 5
  FAST_FORWARD_RELEASE = 6
  REWIND_PRESS = 7
  REWIND_RELEASE = 8
