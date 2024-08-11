import socket

from enum import Enum
from .helpers import NestedEnum, _bytesToMacAddress, _applyBitmask, _macAddressToBytes, _bytesToHexString


class BoseDevice:
  PORT = 8
  
  def __init__(self, macAddress):
    self.macAddress = macAddress
  
    self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    self.socket.connect((self.macAddress, self.PORT))


  ###########################
  #  COMPOSITES/PROCEDURES  #
  ###########################
  
  
  def startChirp(self):
    self.setChirp(True)

  def stopChirp(self):
    self.setChirp(False)
    
  def startMusicSharing(self):
    pass
  

  #######################
  #  GENERIC FUNCTIONS  #
  #######################

  def getFunctionBlockInfo(self, functionBlock):
    self._sendCommand(functionBlock, self.Function.FUNCTION_BLOCK_INFO, self.Operator.GET)
    return self._parseResponse().decode()
  
  
  ##################
  #  PRODUCT INFO  #
  ##################
  
  def getBmapVersion(self):
    self._sendCommand(self.FunctionBlock.PRODUCT_INFO, self.Function.BMAP_VERSION, self.Operator.GET)
    return self._parseResponse().decode()
  
  def getSupportedFunctionBlocks(self):
    self._sendCommand(self.FunctionBlock.PRODUCT_INFO, self.Function.ALL_FUNCTION_BLOCKS, self.Operator.GET)
    supportBitMask = self._parseResponse()
    return _applyBitmask(self.FunctionBlock, supportBitMask)
  
  def getSupportedFunctionBlockVersions(self):
    self._sendCommand(self.FunctionBlock.PRODUCT_INFO, self.Function.ALL_FUNCTION_BLOCKS, self.Operator.START)
    return [ver.decode() for ver in self._parseResponse(expectList=True)]
  
  def getProductIdVariant(self):
    self._sendCommand(self.FunctionBlock.PRODUCT_INFO, self.Function.PRODUCT_ID_VARIANT, self.Operator.GET)
    return self._parseResponse() # TODO: map to some device variant class or something
  
  def getAllDeviceNumbers(self):
    return self._sendAndParseAll(self.FunctionBlock.PRODUCT_INFO, self.Function.ALL_FUNCTIONS)
  
  def getFirmwareVersion(self):
    return self._sendAndParse(self.FunctionBlock.PRODUCT_INFO, self.Function.FIRMWARE_VERSION, self.Operator.GET)
  
  def getMacAddress(self):
    return self._sendAndParse(self.FunctionBlock.PRODUCT_INFO, self.Function.MAC_ADDRESS, self.Operator.GET)
  
  def getSerialNumber(self):
    return self._sendAndParse(self.FunctionBlock.PRODUCT_INFO, self.Function.SERIAL_NUMBER, self.Operator.GET)
  
  def getHardwareRevision(self):
    return self._sendAndParse(self.FunctionBlock.PRODUCT_INFO, self.Function.HARDWARE_REVISION, self.Operator.GET)
  
  def getComponentDevices(self):
    return self._sendAndParse(self.FunctionBlock.PRODUCT_INFO, self.Function.COMPONENT_DEVICES, self.Operator.GET)
  
  
  ##############
  #  SETTINGS  #
  ##############
  
  def getAllSettings(self):
    return self._sendAndParseAll(self.FunctionBlock.SETTINGS, self.Function.ALL_SETTINGS)
  
  def getDeviceName(self):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.DEVICE_NAME, self.Operator.GET)
  
  def setDeviceName(self, name):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.DEVICE_NAME, self.Operator.SET_GET, *name.encode())
  
  def getVoicePrompts(self):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.VOICE_PROMPTS, self.Operator.GET)
  
  def setVoicePrompts(self, config):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.VOICE_PROMPTS, self.Operator.SET_GET, *config._getPayload())
  
  def getStandbyTimer(self):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.STANDBY_TIMER, self.Operator.GET)
  
  def setStandbyTimer(self, time):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.STANDBY_TIMER, self.Operator.SET_GET, time)
  
  def getCnc(self):
    numberOfSteps, currentStep = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.CNC, self.Operator.GET)
    return numberOfSteps, currentStep
  
  def setCnc(self, numberOfSteps, currentStep):
    numberOfSteps, currentStep = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.CNC, self.Operator.SET_GET, numberOfSteps, currentStep)
    return numberOfSteps, currentStep
  
  def getAnr(self):
    noiseCancellingLevel, supportedLevels = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.ANR, self.Operator.GET)
    return noiseCancellingLevel, supportedLevels
  
  def setAnr(self, noiseCancellingLevel):
    noiseCancellingLevel, supportedLevels = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.ANR, self.Operator.SET_GET, noiseCancellingLevel.value)
    return noiseCancellingLevel, supportedLevels
  
  def getBassControl(self):
    minStep, maxStep, currentStep = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.BASS_CONTROL, self.Operator.GET)
    return minStep, maxStep, currentStep
  
  def setBassControl(self, currentStep):
    minStep, maxStep, currentStep = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.BASS_CONTROL, self.Operator.SET_GET, currentStep)
    return minStep, maxStep, currentStep
  
  def getAlerts(self):
    ringtoneEnabled, hapticsEnabled = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.ALERTS, self.Operator.GET)
    return ringtoneEnabled, hapticsEnabled
    
  def setAlerts(self, ringtoneEnabled, hapticsEnabled):
    ringtoneEnabled, hapticsEnabled = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.ALERTS, self.Operator.SET_GET, ringtoneEnabled | (hapticsEnabled << 1))
    return ringtoneEnabled, hapticsEnabled
  
  def getButtons(self):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.BUTTONS, self.Operator.GET)
  
  def setButtons(self, config):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.BUTTONS, self.Operator.SET_GET, *config._getPayload())
  
  def getMultipoint(self):
    isSupported, isEnabled = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.MULTIPOINT, self.Operator.GET)
    return isSupported, isEnabled
  
  def setMultipoint(self, isSupported, isEnabled):
    isSupported, isEnabled = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.MULTIPOINT, self.Operator.SET_GET, isEnabled | (isSupported << 1))
    return isSupported, isEnabled
  
  def getSidetone(self):
    persist, sidetoneLevel, supportedSidetoneLevels = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.SIDETONE, self.Operator.GET)
    return persist, sidetoneLevel, supportedSidetoneLevels

  def setSidetone(self, persist, sidetoneLevel):
    persist, sidetoneLevel, supportedSidetoneLevels = self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.BUTTONS, self.Operator.SET_GET, persist, sidetoneLevel)
    return persist, sidetoneLevel, supportedSidetoneLevels
  
  def getImuVolumeControl(self):
    return self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.IMU_VOLUME_CT, self.Operator.GET)
    
  def setImuVolumeControl(self, isEnabled):
    self._sendAndParse(self.FunctionBlock.SETTINGS, self.Function.IMU_VOLUME_CT, self.Operator.SET_GET, isEnabled)
    
    
  #####################
  #  Firmware Update  #
  #####################
  
  # I will not attempt to write FW-Update code and i will NOT be responsible for bricked devices if you do
  
  
  #######################
  #  Device Management  #
  #######################
  
  def connectDevice(self, macOfOtherDevice):
    self._sendCommand(self.FunctionBlock.DEVICE_MANAGEMENT, self.Function.CONNECT_DEV, self.Operator.START, 0, *_macAddressToBytes(macOfOtherDevice))
    return _bytesToHexString(self._parseResponse()) # TODO
  
  def connectDeviceAndKeep(self, macOfOtherDevice, productTypeOfOtherDevice, macOfDeviceToKeep):
    b1 = ((productTypeOfOtherDevice.value << 7) | 0b10000) & 255
    self._sendCommand(self.FunctionBlock.DEVICE_MANAGEMENT, self.Function.CONNECT_DEV, self.Operator.START, b1, *_macAddressToBytes(macOfOtherDevice), *_macAddressToBytes(macOfDeviceToKeep))
    self._parseResponse() # Start
    return _bytesToHexString(self._parseResponse())
    #return _bytesToHexString(self._parseResponse()) # TODO
  
  def disconnectDevice(self, macOfOtherDevice):
    pass # TODO
  
  def removeDevice(self, macOfOtherDevice):
    pass # TODO
  
  def listDevices(self):
    self._sendCommand(self.FunctionBlock.DEVICE_MANAGEMENT, self.Function.LIST_DEVICES, self.Operator.GET)
    response = self._parseResponse()
    device1Connected = bool(response[0] & 0b01)
    device2Connected = bool(response[0] & 0b10)
    macAddresses = [_bytesToMacAddress(response[i:i+6]) for i in range(1, len(response), 6)]
    return (device1Connected, device2Connected), macAddresses
  
  def getDeviceInfo(self, macOfConnectedDevice):
    self._sendCommand(self.FunctionBlock.DEVICE_MANAGEMENT, self.Function.DEVICE_INFO, self.Operator.GET, *_macAddressToBytes(macOfConnectedDevice))
    return self.PairedDevice(self._parseResponse())
  
  def getExtendedDeviceInfo(self, macOfConnectedDevice):
    self._sendCommand(self.FunctionBlock.DEVICE_MANAGEMENT, self.Function.DEVICE_INFO_EXT, self.Operator.GET, *_macAddressToBytes(macOfConnectedDevice))
    return self._parseResponse()
  
  def clearDeviceList(self):
    pass
  
  def getPairingMode(self):
    pass
  
  def setPairingMode(self):
    pass
  
  def getLocalMacAddress(self):
    pass

  def prepareP2P(self):
    pass
  
  def getP2PMode(self):
    pass
  
  def setP2PMode(self, p2pMode):
    pass
  
  def startRouting(self):
    pass

  
  #############
  #  Control  #
  #############
  
  def getAllControls(self):
    return self._sendAndParseAll(self.FunctionBlock.CONTROL, self.Function.ALL_CONTROLS)
  
  def getChirp(self):
    isInProgress, stopReason = self._sendAndParse(self.FunctionBlock.CONTROL, self.Function.CHIRP, self.Operator.GET)
    return isInProgress, stopReason
  
  def setChirp(self, chirping):
    self._sendAndParse(self.FunctionBlock.CONTROL, self.Function.CHIRP, self.Operator.START, chirping)
  
  
  class Operator(Enum):
    SET     = 0x00
    GET     = 0x01
    SET_GET = 0x02
    STATUS  = 0x03
    ERROR   = 0x04
    START   = 0x05
    FINAL   = 0x06
    PROCESS = 0x07
    
  
  class FunctionBlock(Enum):
    PRODUCT_INFO      = 0x00
    SETTINGS          = 0x01
    STATUS            = 0x02
    FIRMWARE_UPDATE   = 0x03
    DEVICE_MANAGEMENT = 0x04
    AUDIO_MANAGEMENT  = 0x05
    _CALL_MANAGEMENT  = 0x06
    CONTROL           = 0x07
    _DEBUG            = 0x08
    NOTIFICATIONS     = 0x09
    _RESERVED_1       = 0x0a
    _RESERVED_2       = 0x0b
    HEARING_ASSISTANCE= 0x0c
    DATA_COLLECTION   = 0x0d
    HEART_RATE        = 0x0e
    VOICE_PERSONAL_ASSISTANT = 0x10
    AUGMENTED_REALITY = 0x15

  class Function(Enum):
    FUNCTION_BLOCK_INFO = 0x00
    
    BMAP_VERSION        = 0x01
    ALL_FUNCTION_BLOCKS = 0x02
    PRODUCT_ID_VARIANT  = 0x03
    ALL_FUNCTIONS       = 0x04
    FIRMWARE_VERSION    = 0x05
    MAC_ADDRESS         = 0x06
    SERIAL_NUMBER       = 0x07
    HARDWARE_REVISION   = 0x0a
    COMPONENT_DEVICES   = 0x0b
    
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
    
    CONNECT_DEV     = 0x01
    DISCONNECT_DEV  = 0x02
    REMOVE_DEV      = 0x03
    LIST_DEVICES    = 0x04
    DEVICE_INFO     = 0x05
    DEVICE_INFO_EXT = 0x06
    CLEAR_DEV_LIST  = 0x07
    PAIRING_MODE    = 0x08
    LOCAL_MAC_ADDR  = 0x09
    P2P_PREPARE     = 0x0a
    P2P_MODE        = 0x0b
    P2P_ROUTING     = 0x0c
    
    ALL_CONTROLS = 0x01
    CHIRP        = 0x02
    
    
  class VoicePromptSetting:
    CAN_CHANGE = 0b10000000
    IS_ENABLED = 0b00100000
    LANGUAGE   = 0b00011111
    
    class Language(Enum):
      EN_UK = 0x00 # English (U.K.)
      EN_US = 0x01 # English (U.S.)
      FR    = 0x02 # French
      IT    = 0x03 # Italian
      DE    = 0x04 # German
      ES_EU = 0x05 # Spanish (E.U.)
      ES_MX = 0x06 # Spanish (M.X.)
      PT    = 0x07 # Portuguese
      ZH    = 0x08 # Mandarin
      KO    = 0x09 # Korean
      RU    = 0x0a # Russian
      PL    = 0x0b # Polish
      HE    = 0x0c # Hebrew
      TK    = 0x0d # Turkish
      NL    = 0x0e # Dutch
      JA    = 0x0f # Japanese
      CA    = 0x10 # Cantonese
      AR    = 0x11 # Arabic
      SV    = 0x12 # Swedish
      DA    = 0x13 # Danish
      NO    = 0x14 # Norwegian
      SK    = 0x15 # Finnish
    
    def __init__(self, bytes):
      b1 = bytes[0]
      self.canChange = bool(b1 & self.CAN_CHANGE)
      self.isEnabled = bool(b1 & self.IS_ENABLED)
      self.language = self.Language(b1 & self.LANGUAGE)
      supportedLanguagesBitmask = bytes[1:]
      self.supportedLanguages = _applyBitmask(self.Language, supportedLanguagesBitmask)
      
    def _getPayload(self):
      b = self.language.value & self.LANGUAGE
      if (self.isEnabled):
        b |= self.IS_ENABLED
      return bytes([b])
    
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
      
    DEFAULT_BUTTON_ID = 16  # idk why
    DEFAULT_EVENT_TYPE = 4  # idk why
    DEFAULT_FUNCTION = ActionButtonModes.NOT_CONFIGURED
    DEFAULT_FUNCTIONS = []
      
    def __init__(self, bytes):
      self.isConfigurable = False
      self.buttonId = self.DEFAULT_BUTTON_ID
      self.buttonEventType = self.DEFAULT_EVENT_TYPE
      self.configuredFunctionality = self.DEFAULT_FUNCTION
      self.supportedFunctionality = self.DEFAULT_FUNCTIONS
      
      if (len(bytes) == 1):  # idk why,  but this seems to be an indicator, that the button is not configurable right now
        return
      
      self.isConfigurable = True
      self.buttonId = bytes[0]
      self.buttonEventType = bytes[1]
      self.configuredFunctionality = self.ActionButtonModes(bytes[2])
      self.supportedFunctionality = _applyBitmask(self.ActionButtonModes, bytes[3:])
      
    def _getPayload(self):
      return bytes([self.buttonId, self.buttonEventType, self.configuredFunctionality.value])
      
  class SidetoneLevel(Enum):
    OFF    = 0
    HIGH   = 1
    MEDIUM = 2
    LOW    = 3
    
  class PairedDevice:
    class ProductType(Enum):
      HEADPHONES = 1
      SPEAKER = 2
    
    def __init__(self, bytes):
      self.macAddress = _bytesToMacAddress(bytes[:6])
      self.isConnected   = bool(bytes[6] & 0b0001)
      self.isLocalDevice = bool(bytes[6] & 0x0010)
      self.isBoseProduct = bool(bytes[6] & 0x0100)
      self.productType = None
      self.productId = None
      self.productVariant = None
      
      pos = 9 # if it is a normal device, the name starts at pos 9
      if self.isBoseProduct:
        pos = 10 # if it is a bose device, the name starts at pos 10
        self.productType = self.ProductType((bytes[6] >> 7) & 0b01) # can only ever be headphones apparently, since there is only one bit, but what about the second bit needed to represent speaker = 2 = 0b10?
        self.productId = (bytes[7] << 8) | bytes[8]
        self.productVariant = bytes[9]
      
      self.name = bytes[pos:].decode()
    
  class ChirpStopReason(Enum):
    NEVER_SAW_CHIRP = 0
    USER_PUSHED_BUTTON = 1
    TIMED_OUT = 2
    STOPPED = 3
    USER_REMOVED_BUD = 4
    
    
    
  def _sendCommand(self, functionBlock, function, operator, *payload):
    self.socket.send(bytes([functionBlock.value, function.value, operator.value, len(payload), *payload]))
  
  def _parseResponse(self, *, withFunction=False, expectList=False, listWithFunction=False):
    # TODO: maybe add some check that the result matches the request or something?
    _, function = self.socket.recv(2)
    status = self.socket.recv(1)[0]
    length = self.socket.recv(1)[0]
    payload = self.socket.recv(length)

    if (status == BoseDevice.Operator.ERROR.value):
      raise Exception(f"Invalid response, error code: {payload[0]}")
    elif (status == BoseDevice.Operator.START.value or expectList):
      data = []
      while True:
        part = self._parseResponse(withFunction=listWithFunction)
        if part is None:
          break
        data.append(part)
      return data
    elif (status == BoseDevice.Operator.STATUS.value):
      if withFunction:
        return function, payload
      return payload
    elif (status == BoseDevice.Operator.PROCESS.value):
      return self._parseResponse(withFunction=withFunction, expectList=expectList, listWithFunction=listWithFunction)
    elif (status == BoseDevice.Operator.FINAL.value):
      return None
    
    raise Exception(f"Encountered illegal state, response type/status: {status}")
  
  def _sendAndParse(self, functionBlock, function, operator, *payload):
    self._sendCommand(functionBlock, function, operator, *payload)
    return self._FUNCTIONS[functionBlock][function.value][1](self._parseResponse())
  
  def _sendAndParseAll(self, functionBlock, function):
    self._sendCommand(functionBlock, function, self.Operator.START)
    values = self._parseResponse(expectList=True, listWithFunction=True)
    values = {k: f(v) for k, f, v in map(lambda x: (*self._FUNCTIONS[functionBlock].get(x[0]), x[1]), values)} # apply the correct transformation to each component -> mac address should be converted using  _bytesToMacAddress, everything else simply bytes.decode
    return values

  _FUNCTIONS = {
    FunctionBlock.PRODUCT_INFO: {
      Function.FIRMWARE_VERSION: bytes.decode,
      Function.MAC_ADDRESS: _bytesToMacAddress,
      Function.SERIAL_NUMBER: bytes.decode,
      Function.HARDWARE_REVISION: bytes.decode, # TODO
      Function.COMPONENT_DEVICES: bytes.decode, # TODO
    },
    FunctionBlock.SETTINGS: {
      Function.DEVICE_NAME: lambda x: x[1:].decode(),
      Function.VOICE_PROMPTS: lambda x: BoseDevice.VoicePromptSetting(x),
      Function.STANDBY_TIMER: lambda x: x[0],
      Function.CNC: lambda x: (x[0], x[1]),
      Function.ANR: lambda x: (BoseDevice.AnrLevel(x[0]), _applyBitmask(BoseDevice.AnrLevel, x[1:])),
      Function.BASS_CONTROL: lambda x: (x[0], x[1], x[2]),
      Function.ALERTS: lambda x: (bool(x[0] & 0b01), bool(x[0] & 0b10)),
      Function.BUTTONS: lambda x: BoseDevice.ActionButtonSetting(x),
      Function.MULTIPOINT: lambda x: (bool(x[0] & 0b10),  bool(x[0] & 0x01)), # TODO
      Function.SIDETONE: lambda x: (x[0], BoseDevice.SidetoneLevel(x[1]), _applyBitmask(BoseDevice.SidetoneLevel, x[2:])),
      Function.IMU_VOLUME_CT: lambda x: bool(x),
    },
    FunctionBlock.CONTROL: {
      Function.CHIRP: lambda x: (bool(x[0] & 1), BoseDevice.ChirpStopReason((x[0] >> 1) & 0b1111111))
    }
  }
  _FUNCTIONS = {ko: {ki.value: [ki, vi] for ki, vi in vo.items()} for ko, vo in _FUNCTIONS.items()}