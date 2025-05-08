import typing
from enum import Enum, IntFlag
from ...helpers import classproperty, applyBitmask
from ... import basetypes as bt

# operators are what to do with a given function/command
# for example, the command VOLUME within the AUDIO_CONTROL function block can be used with the GET, (SET unsure?) and SET_GET operator
# some operators can only be received and not sent, i.e.: STATUS, ERROR, (START?, FINAL?, PROCESS? unsure)
class Operator(Enum):
  SET     = 0
  GET     = 1
  SET_GET = 2
  STATUS  = 3
  ERROR   = 4
  START   = 5
  FINAL   = 6
  PROCESS = 7
  
  def matchesOperator(self, operatorOrByte: int|typing.Self) -> bool:
    if isinstance(operatorOrByte, Operator):
      return self.matchesOperator(operatorOrByte.value)
    return self.value == operatorOrByte
  
  def isError(self):
    return self == self.__class__.ERROR 

_FUNCTION_BLOCK_INFO = 0x00

# this class/interface defines what a command should look like to be comparable with other commands
# it should be an enum, so that one can use it as follows: CommandGroup1.COMMAND.matchesCommand(...)    (assuming CommandGroup1 inherits from _CommandComparableLike, i.e.: class CommandGroup1(_CommandComparableLike, Enum): ...)
# it should implement a function that checks if a given command (given as _CommandComparableLike) is equivalent to another command (given in bytes)
# this is used to do something described right before def _FunctionBlockEnum and is pretty cursed
class CommandComparableLike(Enum):
  def __init__(self, *args, **kwargs):
    self.commands: typing.Type[CommandLike]
  def matchesCommand(self, commandOrFunctionBlockByte: typing.Self|int, functionByte: None|int=None) -> bool:
      if isinstance(commandOrFunctionBlockByte, CommandLike):
        return self.matchesCommand(commandOrFunctionBlockByte.functionBlock.value, commandOrFunctionBlockByte.value)
      if isinstance(commandOrFunctionBlockByte, FunctionBlock):
        return self.matchesCommand(commandOrFunctionBlockByte.value)
      
      return self._matchesCommand(commandOrFunctionBlockByte, functionByte)
    
  def _matchesCommand(self, functionBlockByte: int, functionByte: None|int=None) -> bool:
    raise NotImplementedError("subclasses (i.e. command enums) should implement this")
  
# something that actually represents a fully fledged command should not only be comparable to other commands (i.e. inherit from _CommandComparableLike)
# but should also always contain a variable called functionBlock, to represent which function block it belongs to
# therefore, a command such as _Audio_Function.NOW_PLAYING is uniquely identified by the combination of function block value (0x05) and the function value (0x06)
# and can thus be differentiated from _ProductInfo_Function.MAC_ADDRESS which also has a function value of 0x06, but a different function block value (0x00)
class CommandLike(CommandComparableLike):
  def __init__(self, *args, **kwargs):
    self.functionBlock: FunctionBlock
    
  if typing.TYPE_CHECKING: # when type checking, we insert the constant enum item FUNCTION_BLOCK_INFO, that is available on every function block. it is only for type checking purposes (see bose -> device -> BoseDevice._getFunctionBlockInfo() for use case)
    FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  
  def _matchesCommand(self, functionBlockByte: int, functionByte: int) -> bool:
      return (self.functionBlock.value == functionBlockByte) and (self.value == functionByte) 
  
# an enum of all function blocks, these are used to split all functions into useful groups
# these function blocks also help differentiate which functionality a peripheral supports, as the peripheral will only list supported function blocks when querying _ProductInfo_Function.ALL_FUNCTION_BLOCKS
# so one can quickly determine whether their headphones have a heart rate sensor or not (_FunctionBlock.HEART_RATE)
class FunctionBlock(CommandComparableLike):
  PRODUCT_INFO       = 0x00
  SETTINGS           = 0x01
  STATUS             = 0x02
  FIRMWARE_UPDATE    = 0x03
  DEVICE_MANAGEMENT  = 0x04
  AUDIO_MANAGEMENT   = 0x05
  _CALL_MANAGEMENT   = 0x06
  CONTROL            = 0x07
  _DEBUG             = 0x08
  NOTIFICATIONS      = 0x09
  _RESERVED_1        = 0x0a
  _RESERVED_2        = 0x0b
  HEARING_ASSISTANCE = 0x0c
  DATA_COLLECTION    = 0x0d
  HEART_RATE         = 0x0e
  VOICE_PERSONAL_ASSISTANT = 0x10
  AUGMENTED_REALITY  = 0x15
  
  def _matchesCommand(self, functionBlockByte: int, functionByte: int) -> bool:
    return self.value == functionBlockByte
  
  # defines a "type", that is basically an enum but ensures it has an additional static variable "functionBlock" -> can be used for Command/Function Enums to hold the information which FunctionBlock they correspond to
  # the function block is passed during class declaration which is really cursed but it is the only way, as otherwise we would have to pass this argument during enum instantiation which defeats the purpose
  @property
  def _FunctionEnum(self):
    functionBlock = self
    class _Enum(CommandLike):
      def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.functionBlock = functionBlock
      def __init_subclass__(cls):
        functionBlock.commands = cls
        return super().__init_subclass__()
  
    return _Enum
  
class ProductInfo_Function(FunctionBlock.PRODUCT_INFO._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  BMAP_VERSION        = 0x01
  ALL_FUNCTION_BLOCKS = 0x02
  PRODUCT_ID_VARIANT  = 0x03
  ALL_FUNCTIONS       = 0x04
  FIRMWARE_VERSION    = 0x05
  MAC_ADDRESS         = 0x06
  SERIAL_NUMBER       = 0x07
  HARDWARE_REVISION   = 0x0a
  COMPONENT_DEVICES   = 0x0b

class Settings_Function(FunctionBlock.SETTINGS._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  ALL_SETTINGS  = 0x01
  DEVICE_NAME   = 0x02
  VOICE_PROMPTS = 0x03
  STANDBY_TIMER = 0x04
  CNC           = 0x05
  ANR           = 0x06
  BASS_CONTROL  = 0x07
  ALERTS        = 0x08
  BUTTONS       = 0x09
  MULTIPOINT    = 0x0a
  SIDETONE      = 0x0b
  IMU_VOLUME_CT = 0x17
  
class Status_Function(FunctionBlock.STATUS._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL_FUNCTIONS   = 0x01
  BATTERY_LEVEL       = 0x02
  AUX_CABLE_DETECTION = 0x03
  MIC_LEVEL           = 0x04
  CHARGER_DETECT      = 0x05
  
class FirmwareUpdate_Function(FunctionBlock.FIRMWARE_UPDATE._FunctionEnum):
  # WARNING: I AM NOT RESPONSIBLE FOR BRICKING YOUR DEVICE IF YOU USE THE FIRMWARE UPDATE OPTIONS WRONG!
  # TODO: these functions are not implemented yet, anyone brave enough to potentially brick their headphones is welcome to try :) (SEE WARNING)
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  STATE         = 0x01
  INIT          = 0x02
  DATA_TRANSFER = 0x03
  SYNCHRONIZE   = 0x04
  VAILDATE      = 0x05
  RUN           = 0x06
  RESET         = 0x07
  
class DeviceManagement_Function(FunctionBlock.DEVICE_MANAGEMENT._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  CONNECT           = 0x01
  DISCONNECT        = 0x02
  REMOVE_DEVICE     = 0x03
  LIST_DEVICES      = 0x04
  INFO              = 0x05
  INFO_EXTENDED     = 0x06
  CLEAR_DEVICE_LIST = 0x07
  PAIRING_MODE      = 0x08
  LOCAL_MAC_ADDRESS = 0x09
  PREPARE_P2P       = 0x0a
  P2P_MODE          = 0x0b
  ROUTING           = 0x0c
  
class Audio_Function(FunctionBlock.AUDIO_MANAGEMENT._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  SOURCE         = 0x01
  ALL_AUDIO_INFO = 0x02
  CONTROL        = 0x03
  STATUS         = 0x04
  VOLUME         = 0x05
  NOW_PLAYING    = 0x06
  
class Control_Function(FunctionBlock.CONTROL._FunctionEnum):
  FUNTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL = 0x01
  CHIRP   = 0x02
  
class Notifications_Function(FunctionBlock.CONTROL._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  RESET             = 0x01
  BY_FUNCTION_BLOCK = 0x02
  BY_FUNCTION       = 0x03
  PERIODIC          = 0x04
  
class HearingAssistance_Function(FunctionBlock.HEARING_ASSISTANCE._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  WDRC_BRIEF_UPDATE       = 0x01
  WDRC_INDIVIDUAL_UPDATE  = 0x02
  DIRECTIONALITY          = 0x03
  DIRECTIONALITY_SETTINGS = 0x04
  NR_CONTROL              = 0x05
  NR_SETTINGS             = 0x06
  MAPPED_SETTINGS_STANDARD_MODE = 0x07
  WDRC_BAND_DEFINITIONS   = 0x08
  EQ_BAND_DEFINITIONS     = 0x09
  SUB_PROCESSOR_VERSION   = 0x0a
  MUTING                  = 0x0b
  BOOST_EQ                = 0x0c
  LIMITS                  = 0x0d
  SUB_PROCESSOR_STATUS    = 0x0e
  MAPPED_SETTINGS_MODE    = 0x0f
  MAPPED_SETTINGS_OFFSET_CONTROL_MODE = 0x10
  GLOBAL_MUTE             = 0x11
  ALGORITHM_CONTROL       = 0x12
  LIVE_METRICS            = 0x13
  DOFF_AUTO_OFF_TIME      = 0x14
  
class DataCollection_Function(FunctionBlock.DATA_COLLECTION._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL = 0x01
  RECORDS = 0x02
  PAUSE   = 0x03
  CLEAR   = 0x04
  UID     = 0x05
  ENABLE  = 0x06
  
class HeartRate_Function(FunctionBlock.HEART_RATE._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL          = 0x01
  HEART_RATE       = 0x02
  HEART_RATE_STATS = 0x03
  SPEED_DISTANCE   = 0x04
  STEP_RATE_STATS  = 0x05
  CALORIES         = 0x06
  VO2              = 0x07
  USER_INFO        = 0x08
  WORKOUT_INFO     = 0x09
  HEART_RATE_READING_RELIABILITY = 0x0a
  OPTICAL_SENSOR_STATUS = 0x0b
  POST_STATUS      = 0x0c
  CALIBRATION_INFO = 0x0d
  FIRMWARE_VERSION = 0x0e
  HARDWARE_INFO    = 0x0f
  
class VoicePersonalAssistant_Function(FunctionBlock.VOICE_PERSONAL_ASSISTANT._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL        = 0x01
  SUPPORTED_VPAS = 0x02
  
class AugmentedReality_Function(FunctionBlock.AUGMENTED_REALITY._FunctionEnum):
  FUNCTION_BLOCK_INFO = _FUNCTION_BLOCK_INFO
  GET_ALL             = 0x01
  AR_STREAMING_STATUS = 0x02

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


class _ValueList[K, V]:
  def __init__(self):
    self._values0 = dict[K, V]()
    self._values1 = dict[K, V]()
    self._pointer = 0
    self._write = False
    self._isWritten = False
    
  @property
  def values(self) -> dict[K, V]:
    self._getValues()
    
  @property
  def writeValues(self) -> dict[K, V]|None:
    if not self._write:
      return
    return self._getValues(True)
  
  def writeValue(self, key: K, value: V):
    values = self.writeValues
    if not values:
      return
    values[key] = value
    
  def hasValue(self, key: K):
    return key in self.values
  
  def getValue(self, key: K, default: V|None=None):
    return self.values.get(key, default)
    
  def _switchPointer(self, pointer: int|None=None, write: bool=True) -> int:
    if pointer is None:
      pointer = self._pointer
    pointer = (pointer+1) % 2
    if write:
      self._pointer = pointer
    return pointer
    
    
  def _getValues(self, getWriteValues: bool=False) -> dict:
    pointer = self._pointer
    if getWriteValues:
      pointer = self._switchPointer(pointer, write=False)
    if pointer == 0:
      return self._values0
    return self._values1
    
  def startWrite(self):
    self._getValues(True).clear()
    self._write = True
    
  def finishWrite(self):
    self._write = False
    self._switchPointer()
    self._isWritten = True
    
  def reset(self):
    self._write = False
    self._isWritten = False
    self._values0.clear()
    self._values1.clear()

class _ParserList:
  def __init__(self):
    self._parsers = dict()
    
  @classmethod
  def _toParserKey(cls, *args):
      if len(args) == 1:
        args = args[0]
        
      if len(args) == 2:
        command, operator = args
        return cls._toParserKey(command.functionBlock.value, command.value, operator.value)
      if len(args) == 3:
        return bytes(args)
  
  def isEmpty(self):
    return len(self._parsers) == 0
  
  # the following functions (_get and _set) are ugly, but they ensure that one can set parsers in the following (edge) cases:
  #  - for a given command (function block + function) and a given operator [-> e.g. when receiving a [VOLUME] [STATUS] packet]
  #  - for a given command (function block + function) and all operators [-> no valid use-case yet]
  #  - for all commands/functions of a given function block and a given operator [-> e.g. when one specific function block needs error handling]
  #  - for all commands with the same function but on different function blocks [-> e.g. when parsing the [FUNCTION_BLOCK_INFO] which is present on all function blocks]
  #  - for multiple commands and a given operator [-> e.g. parsing mac addresses is the same for different commands]
  #  - for a command and multiple operators [-> e.g. a function may expect an error and can handle both the result and a potential error]
  def _get(self, key: bytes, default=None):
    k1, k2, k3 = key
    for i2 in [k2, None]:
      for i1 in [k1, None]:
        for i3 in [k3, None]:
          parsers1 = self._parsers.get(i1)
          if not parsers1: continue
          parsers2 = parsers1.get(i2)
          if not parsers2: continue
          parser = parsers2.get(i3)
          if not parser: continue
          return parser
    return default
  
  @classmethod
  def _isIterable(cls, x):
    return hasattr(x, "__getitem__")
  
  @classmethod
  def _toIterable(cls, x):
    if cls._isIterable(x):
      return x
    return [x]
  
  def _set(self, key: tuple[None|tuple[tuple[int, None|int]|tuple[None, int]], None|int|typing.Iterable[int]], value: typing.Callable):
    k12, k3 = key
    k12 = self._toIterable(k12)
    k3 = self._toIterable(k3)
    
    for i12 in k12:
      if i12 is None:
        i1 = None
        i2 = None
      else:
        i1, i2 = i12
        
      if not i1 in self._parsers:
        self._parsers[i1] = dict()
      parsers2 = self._parsers[i1]
      
      if not i2 in parsers2:
        parsers2[i2] = dict()
      parsers3 = parsers2[i2]
        
      for i3 in k3:
        parsers3[i3] = value
  
  def __getitem__(self, index: tuple[CommandLike, Operator]|tuple[int,int,int]) -> typing.Callable|None:
    key = self._toParserKey(index)
    return self._get(key)
  
  def __setitem__(self, index: tuple[None|typing.Iterable[CommandLike|tuple[int, int|None]|tuple[None, int]], None|Operator|typing.Iterable[Operator]], value: typing.Callable):
    commands = self._toIterable(index[0])
    operators = self._toIterable(index[1])
    
    commands = [c if self._isIterable(c) else [None, None] if c is None else [c.functionBlock.value, c.value] for c in commands]
    operators = [o if isinstance(o, int) or o is None else o.value for o in operators]
    
    self._set([commands, operators], value)