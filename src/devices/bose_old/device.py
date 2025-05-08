import time
import errno
import socket
import typing
import asyncio
from .types import FunctionBlock, Operator, CommandLike, CommandComparableLike, _FUNCTION_BLOCK_INFO, _ValueList, _ParserList
from .types import BoseProductId, BoseProduct, DeviceName, VoicePromptSetting, VolumeData
from .types import ProductInfo_Function as F_PROD_INFO, Settings_Function as F_SETTINGS, Status_Function as F_STATUS, Audio_Function as F_AUDIO
from .helpers import parser, unknownResponse
from ..base.asyncdev import Device
from ...helpers import AsyncCachedValue, applyBitmask, listToBitmask
from ...basetypes import VersionMajorMinorPatch as VersionMMP, MacAddress, SerialNumber

FB = FunctionBlock
OP = Operator

class BoseDevice(Device):
  _PORT = 8
  _TIMEOUT = 10
  _TIME_PER_WAIT_STEP = 0.05
  _SIZE_HEADER = 4
  _POS_SIZE = 3
  
  def __init__(self, macAddress, *, port=_PORT):
    self.macAddress = macAddress
    self._port = port
  
    self._isConnected = False
    self._lastParseSuccessful = False
    self._createCaches()
  
    self._socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    self._socket.setblocking(False)
    self._buffer = bytearray()
    
  async def connect(self):
    timeEnd = time.time() + self._TIMEOUT
    while time.time() <= timeEnd:
      err = self._socket.connect_ex((self.macAddress, self._port))
      if err in [errno.EISCONN]:
        self._isConnected = True
        await self.getBmapVersion()
        return
      await asyncio.sleep(self._TIME_PER_WAIT_STEP)
    
    raise TimeoutError("could not connect to device within specified time")
    
  async def disconnect(self):
    with self._sem_socket:
      self._socket.close()
    self._isConnected = False
  
  
  async def isConnected(self) -> bool:
    return self._isConnected
  
  async def getBmapVersion(self) -> VersionMMP:
    return await self._bmapVersion.value
  
  async def getFirmwareVersion(self) -> VersionMMP:
    return await self._firmwareVersion.value
  
  async def getMacAddress(self) -> MacAddress:
    return await self._macAddress.value
  
  async def getSerialNumber(self) -> SerialNumber:
    return await self._serialNumber.value
  
  async def getProductId(self) -> BoseProductId:
    return await self._productId.value
  
  async def getDeviceName(self) -> str:
    return (await self._deviceName.value).name
  
  async def getSupportedLanguages(self):
    return (await self._voicePrompts.value).supportedLanguages
  
  async def getLanguage(self):
    return (await self._voicePrompts.value).language
  
  async def setLanguage(self, language):
    return (await self._changeVoicePrompts(language=language)).language

  async def setVoicePromptEnabled(self, enabled):
    return (await self._changeVoicePrompts(isEnabled=enabled)).isEnabled
  
  async def getStandbyTime(self):
    return await self._standbyTime.value
  
  async def setStandbyTime(self, time):
    return await self._setAndGetStandbyTime(time)
  
  async def getBatteryLevel(self):
    return await self._batteryLevel.value
  
  async def isChargerConnected(self):
    return await self._chargerPresent.value
  
  async def isAuxCableConnected(self):
    return await self._auxCablePresent.value
  
  async def getVolume(self) -> int:
    return (await self._volume.value).percentage
  
  async def setVolume(self, volume):
    return (await self._setAndGetVolume(volume)).percentage
  
  
  ###########################################################################
  # Internal functions and classes for sending and parsing specific packets #
  ###########################################################################
  
  # [*, 0x00] Function Block Info (supported version for a given function block, i.e. music share is only supported on devices with a higher function block version in _FunctionBlock.DEVICE_MANAGEMENT)
  async def _getFunctionBlockInfo(self, functionBlock: FB):
    return await self._sendCommandAndParseResponse(functionBlock.commands.FUNCTION_BLOCK_INFO, OP.GET, stopCondition=self._fbVersions[functionBlock])
    
  @parser([(None, _FUNCTION_BLOCK_INFO)])
  def _parseFunctionBlockInfo(self, command: CommandLike, _2, data: bytearray):
    self._fbVersions[command.functionBlock].value = VersionMMP.fromString(data.decode())
  
  # [0x00, 0x01] BMAP Version
  async def _getBmapVersion(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.BMAP_VERSION, OP.GET, stopCondition=self._bmapVersion)
  
  @parser(F_PROD_INFO.BMAP_VERSION)
  def _parseBmapVersion(self, _1, _2, data: bytearray):
    self._bmapVersion.value = VersionMMP.fromString(data.decode())
  
  # [0x00, 0x03] Product ID Variant
  async def _getProductIdVariant(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.PRODUCT_ID_VARIANT, OP.GET, stopCondition=self._productId)

  @parser(F_PROD_INFO.PRODUCT_ID_VARIANT)
  def _parseProductIdVariant(self, _1, _2, data: bytearray):
    productId = (data[0] << 8) | data[1]
    variantId = data[2]
    self._productId.value = BoseProduct._getBestFitByBytes(productId, variantId)
  
  # [0x00, 0x05] Firmware Version
  async def _getFirmwareVersion(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.FIRMWARE_VERSION, OP.GET, stopCondition=self._firmwareVersion)
    
  @parser(F_PROD_INFO.FIRMWARE_VERSION)
  def _parseFirmwareVersion(self, _1, _2, data: bytearray):
    self._firmwareVersion.value = VersionMMP.fromString(data.decode())
  
  # [0x00, 0x06] Mac Address
  async def _getMacAddress(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.MAC_ADDRESS, OP.GET, stopCondition=self._macAddress)
    
  @parser(F_PROD_INFO.MAC_ADDRESS)
  def _parseMacAddress(self, _1, _2, data: bytearray):
    self._macAddress.value = MacAddress.fromBytes(data)
    
  # [0x00, 0x07] Serial Number
  async def _getSerialNumber(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.SERIAL_NUMBER, OP.GET, stopCondition=self._serialNumber)
    
  @parser(F_PROD_INFO.SERIAL_NUMBER)
  def _parseSerialNumber(self, _1, _2, data: bytearray):
    self._serialNumber.value = SerialNumber(data.decode())
  
  # [0x00, 0x0a] Hardware Revision
  async def _getHardwareRevision(self):
    return await self._sendCommandAndParseResponse(F_PROD_INFO.HARDWARE_REVISION, OP.GET, stopCondition=self._hardwareRevision)
    
  @parser(F_PROD_INFO.HARDWARE_REVISION)
  def _parseHardwareRevision(self, _1, _2, data: bytearray):
    self._hardwareRevision.value = data.decode()
    
  # [0x00, 0x0b] Component Devices: TODO
  
  
  # [0x01, 0x02] Device Name:
  async def _getDeviceName(self):
    return await self._sendCommandAndParseResponse(F_SETTINGS.DEVICE_NAME, OP.GET, stopCondition=self._deviceName)
  
  @parser(F_SETTINGS.DEVICE_NAME)
  def _parseDeviceName(self, _1, _2, data: bytearray):
    flags, *name = data
    isDefaultName = flags & 0b01
    name = bytes(name).decode()
    self._deviceName.value = DeviceName(name, isDefaultName)
    
  async def _setAndGetDeviceName(self, name: str):
    return await self._sendCommandAndParseResponse(F_SETTINGS.DEVICE_NAME, OP.SET_GET, *name.encode(), stopCondition=self._deviceName)

  # [0x01, 0x03] Voice Prompts:
  async def _getVoicePrompts(self):
    return await self._sendCommandAndParseResponse(F_SETTINGS.VOICE_PROMPTS, OP.GET, stopCondition=self._voicePrompts)
  
  _VP_CAN_CHANGE = 0b10000000 # O.......
  _VP_IS_ENABLED = 0b00100000 # ..O.....
  _VP_LANGUAGE_M = 0b00011111 # ...OOOOO
  @parser(F_SETTINGS.VOICE_PROMPTS)
  def _parseVoicePrompts(self, _1, _2, data: bytearray):
    cel, *languagesBitmask = data
    canChange = bool(cel & self._VP_CAN_CHANGE)
    isEnabled = bool(cel & self._VP_IS_ENABLED)
    language = VoicePromptSetting.Language._getByByte(cel & self._VP_LANGUAGE_M)
    supportedLanguages = applyBitmask(VoicePromptSetting.Language, languagesBitmask, VoicePromptSetting.Language._BYTE_ATTR)
    self._voicePrompts.value = VoicePromptSetting(canChange, isEnabled, language, supportedLanguages)
    
  async def _setAndGetVoicePrompts(self, isEnabled: bool, language: VoicePromptSetting.Language):
    payload = language.byte & self._VP_LANGUAGE_M
    if isEnabled:
      payload |= self._VP_IS_ENABLED
    return await self._sendCommandAndParseResponse(F_SETTINGS.VOICE_PROMPTS, OP.SET_GET, payload, stopCondition=self._voicePrompts)
  
  async def _changeVoicePrompts(self, *, isEnabled: bool|None = None, language: VoicePromptSetting.Language|None = None) -> VoicePromptSetting:
    vp = await self._voicePrompts.value
    isEnabled = vp.isEnabled if isEnabled is None else isEnabled
    language  = vp.language  if language is None  else language
    return await self._setAndGetVoicePrompts(isEnabled, language)
    
  # [0x01, 0x04] Standby Timer
  async def _getStandbyTime(self):
    return await self._sendCommandAndParseResponse(F_SETTINGS.STANDBY_TIMER, OP.GET, stopCondition=self._standbyTime)
  
  @parser(F_SETTINGS.STANDBY_TIMER)
  def _parseStandbyTime(self, _1, _2, data: bytes):
    self._standbyTime.value = data[0]
    
  async def _setAndGetStandbyTime(self, time: int):
    return await self._sendCommandAndParseResponse(F_SETTINGS.STANDBY_TIMER, OP.SET_GET, time, stopCondition=self._standbyTime)
  
  
  # [0x02, 0x02] Battery Level
  async def _getBatteryLevel(self):
    return await self._sendCommandAndParseResponse(F_STATUS.BATTERY_LEVEL,  OP.GET, stopCondition=self._batteryLevel)
  
  @parser(F_STATUS.BATTERY_LEVEL)
  def _parseBatteryLevel(self, _1, _2, data: bytes):
    self._batteryLevel.value = data[0]
    
  # [0x02, 0x03] Aux Cable Detection
  async def _getAuxCable(self):
    return await self._sendCommandAndParseResponse(F_STATUS.AUX_CABLE_DETECTION, OP.GET, stopCondition=self._auxCablePresent)
  
  @parser(F_STATUS.AUX_CABLE_DETECTION)
  def _parseAuxCable(self, _1, _2, data: bytes):
    self._auxCablePresent.value = bool(data and data[0])
    
  # [0x02, 0x04] Mic Level
  async def _getMicLevel(self):
    return await self._sendCommandAndParseResponse(F_STATUS.MIC_LEVEL, OP.GET, stopCondition=self._micLevel)
  
  @parser(F_STATUS.MIC_LEVEL)
  @unknownResponse
  def _parseMicLevel(self, _1, _2, data: bytes):
    self._micLevel.value = data[0]
    
  # [0x02, 0x05] Charger Detection
  async def _getChargerPresent(self):
    return await self._sendCommandAndParseResponse(F_STATUS.CHARGER_DETECT, OP.GET, stopCondition=self._chargerPresent)
  
  @parser(F_STATUS.CHARGER_DETECT)
  def _parseChargerPresent(self, _1, _2, data: bytes):
    self._chargerPresent.value = bool(data and data[0])
  
  # [0x05, 0x05] Volume
  async def _getVolume(self):
    return await self._sendCommandAndParseResponse(FB.AUDIO_MANAGEMENT.commands.VOLUME, OP.GET, stopCondition=self._volume)
    
  @parser(F_AUDIO.VOLUME)
  def _parseVolume(self, _1, _2, data: bytearray):
    maxVolume, curVolume = data
    self._volume.value = VolumeData(curVolume, maxVolume)
  
  async def _calculateActualVolume(self, volume: int) -> int:
    return (await self._volume.getValue(updateIfOutdated=False))._calculateVolumeForBoseDevice(volume)
    
  async def _setVolume(self, volume):
    actualVolume = await self._calculateActualVolume(volume)
    self._sendCommand(F_AUDIO.VOLUME, OP.SET, actualVolume)
    
  async def _setAndGetVolume(self, volume):
    actualVolume = await self._calculateActualVolume(volume)
    return await self._sendCommandAndParseResponse(F_AUDIO.VOLUME, OP.SET_GET, actualVolume, stopCondition=self._volume)
  
  # Unhandled Errors
  @parser(None, OP.ERROR)
  def _parseError(self, _1, _2, data: bytearray):
    raise ValueError(f"peripheral sent an error ({', '.join([f'0x{x:02x}' for x in data])}) that was not handled")
  
  # Internal functions for sending, receiving and parsing packets in general
  
  # send a command to the headphones
  #  - command: anything that has the form of a command (i.e. a functionblock value and a command value); i.e. BoseDevice._AudioControl_Function.VOLUME
  #  - operator: what you want to do on the command/function; i.e. BoseDevice._ProductInfo_Function.SET_GET will change the volume (i.e. SET) and the headphones will immediately respond with the new volume after changing (i.e. GET) without us needing to send an extra packet
  #  - *payload: the data we want to transmit on top of the command/operator;  when changing the volume, one payload value has to be sent, representing the new volume to be
  # example: self._sendCommand(VOLUME, SET_GET, 10)
  def _sendCommand(self, command: CommandLike, operator: Operator, *payload: int, port: int = 0, deviceId: int = 0):
    opd = (operator.value & 0b1111) | (port & 0b11) << 4 | (deviceId & 0b11) << 6
    self._socket.send(bytes([command.functionBlock.value, command.value, opd, len(payload), *payload]))
  
  # will read all new available bytes (that were sent from the headphones to the host) and append then to self._buffer
  def _readAvailableBytes(self) -> int:
    data = bytearray()

    while True:
      try:
        data.extend(self._socket.recv(1))
      except:
        break
      
    self._buffer.extend(data)
    return len(data)
  
  # looks at the front of self._buffer and determines, if there is a valid and complete response to parse
  # if there is a valid response, it removes it from the front and returns it, otherwise this function returns None
  # a valid response has the same structure as a command sent from the host to the headphones, i.e.:
  # FUNCTION_BLOCK, FUNCTION, (RESPONSE_)OPERATOR, PAYLOAD_SIZE, *PAYLOAD
  # where PAYLOAD is a buffer of length PAYLOAD_SIZE
  # TODO: in theory, a race condition could occur here between "sizePayload = ..." and "assert sizePayload == sizePayload2", where another task has already read the same content as the current task, but
  #       1. i cant use asyncio.Lock(), because then the function would have to async lock.acquire() and i dont want to mark this function async
  #       2. i dont want to use threading.Lock() due to its overhead
  def _readFromBufferIfPossible(self) -> tuple[int, int, int, int, bytearray]|None:
    if len(self._buffer) < self._SIZE_HEADER:
      return None
    
    sizePayload = self._buffer[self._POS_SIZE]
    expectedSize = self._SIZE_HEADER + sizePayload
    if len(self._buffer) < expectedSize:
      return None
    
    functionBlock, function, opd, sizePayload2, *payload = self._buffer[:expectedSize]
    assert sizePayload == sizePayload2  # something went horribly wrong and we probably did read some garbage data if those two values do not match up -> prob race condition
    del self._buffer[:expectedSize]
    
    operator = (opd >> 0) & 0b1111  # ....OOOO
    port     = (opd >> 4) & 0b11    # ..OO....
    deviceId = (opd >> 6) & 0b11    # OO......
    
    return functionBlock, function, operator, port, deviceId, sizePayload, bytearray(payload)
  
  # parses a single response using the appropriate parser
  # returns to bools [success, error]
  # where success represents if there was anything to parse
  # and error represents if an error packet (i.e. _Operator.ERROR) was received
  # error can only ever be True if success is True, as the packet cannot be an error packet if no packet has been received
  def _parseResponse(self) -> None|tuple[CommandLike, Operator, bytes]:
    bytesRead = self._readAvailableBytes() # check if we actually read any new data
    if (not self._lastParseSuccessful) and (bytesRead < 1): # a new try at parsing the available data only makes sense when there is actually any new data
      return None
      
    splitBufferData = self._readFromBufferIfPossible()
    if not splitBufferData:
      self._lastParseSuccessful = False
      return None  # there was new data, but it was still not enough to represent a valid bmap response
      
    functionBlock, function, operatorV, port, deviceId, sizePayload, payload = splitBufferData  # there was enough new data to be a valid bmap response
      
    isError = False
    command = None
    try:
      command = FunctionBlock(functionBlock).commands(function)
    except AttributeError:
      isError = True
      print(f"WARNING: no commands were registered for function block 0x{functionBlock:02x}. please verify that there exists an enum item with the value within BoseDevice._FunctionBlock and that there is exactly one enum class within BoseDevice that inherits from _FunctionBlock.<XXX>._FunctionEnum")
    except ValueError:
      isError = True
      print(f"WARNING: either function block (0x{functionBlock:02x}) or function (0x{function:02x}) within function block is not defined. please verify that a function block with the value exists in BoseDevice._FunctionBlock and a function with the value exists in the respective function enum (e.g. BoseDevice._ProductInfo_Function)")

    operator = None
    try:
      operator = Operator(operatorV)
    except ValueError:
      isError = True
      print(f"WARNING: no operator with value 0x{operatorV:02x} was registered. please verify that there is exactly one enum item with the value within BoseDevice._Operator")
      
    if operator.isError():
      isError = True
      self._handleError(payload) # print a warning when encountering an error state

    parser = None
    if command and operator:
      parser = self._PARSERS[command, operator] # determine the correct parser for the response
        
    if parser:
      parser(self, command, operator, payload) # apply the parser to the data/payload -> calculates the actual volume from the raw bytes
    else:
      isError = True
      print(f"WARNING: encountered response with no known parser: {functionBlock}, {function}; please check whether there is a parser function (i.e. _parserXY()) for your desired command and if it is properly decorated using the @_parser decorator")
      if self._PARSERS.isEmpty():
        print(f"WARNING: there are no known parsers at all (i.e. BoseDevice._PARSERS is empty); apparently the @_parser decorator (specifically the __set_name__ method within _parser()) is not properly supported on this python version")
        
    self._lastParseSuccessful = True
        
    return command, operator, payload, isError
  
  # parses all responses, that have been received from the headphones
  # returns only when the response to a given event has been found (e.g. we are waiting for the STATUS response after sending a VOLUME SET_GET packet -> a VOLUME STATUS packet is parsed by _parseVolume() which sets self._volume (AsyncCachedValue) which will set a event that has been requested before sending the GET VOLUME packet via self._volume.addSingleOnChangeEvent())
  # or raises an exception after timing out with no valid response
  async def _parseResponses(self, stopEvent: None|asyncio.Event, stopOnCommandError: None|CommandComparableLike, timeout: int|float|None = _TIMEOUT):
    timeEnd = None if timeout is None else time.time() + timeout
    lastReadSuccessful = True
    
    while (timeEnd is None) or (time.time() <= timeEnd):
      if not lastReadSuccessful:
        # last read was not successful but we reached our goal, so we can assume that no more relevant data is coming after this and we can return
        if (stopEvent is None) or stopEvent.is_set():
          return
        
        # if the last read was not successful but we did not reach our goal yet, we probably still have to wait some more time until the relevant data arrives
        await asyncio.sleep(self._TIME_PER_WAIT_STEP)
        
      lastReadSuccessful = False
      response = self._parseResponse()
      if not response:
        continue
      command, _, _, isError = response

      if isError and stopOnCommandError and stopOnCommandError.matchesCommand(command):
        stopEvent.set()

      lastReadSuccessful = True
    
    if timeout is None:
      return
    raise TimeoutError("did not receive specified command/operator in time")
  
  def _parsePreviousData(self):
    while True:
      response = self._parseResponse()
      if not response:
        break
  
  def _clearPreviousData(self):
    self._parsePreviousData()
    self._buffer.clear()
  
  async def _sendCommandAndParseResponse[T](self, function: CommandLike, operatorSend: Operator, *payload: int, stopCondition:asyncio.Event|AsyncCachedValue[T]|typing.Callable[[], asyncio.Event|typing.Coroutine[typing.Any, typing.Any, asyncio.Event]]) -> T:
    event = stopCondition
    clearEventCallback = None
    if isinstance(stopCondition, AsyncCachedValue):
      event = stopCondition.addSingleOnChangeEvent
      clearEventCallback = stopCondition.removeOnChangeEvent
    if callable(event):
      event = event()
    if asyncio.iscoroutine(event):
      event = await event
      
    try:
      self._sendCommand(function, operatorSend, *payload)
      await self._parseResponses(event, function)
    finally:
      if clearEventCallback:
        clearEventCallback(event)
        
    if isinstance(stopCondition, AsyncCachedValue):
      return await stopCondition.getValue(skipUpdate=True)
    
  def _handleError(self, payload):
    errorCode = payload[0]
    errorMsg = self._ERRORS.get(errorCode, None)
    needsMoreInfo = (not errorMsg) or (errorCode in [0x00, 0xff])
    
    if not errorMsg:
      errorMsg = "Unknown error (invalid error code)"
    
    if needsMoreInfo:
      errorMsg += f" [{', '.join([f'0x{v:02x}' for v in payload])}]"
      
    print(f"WARNING: encountered error (code: 0x{errorCode:02x}) - {errorMsg}")
    
  
  # Caching related stuff
  
  def _createCaches(self):
    _bose = self
    class BoseCachedValue[T](AsyncCachedValue[T]): # a custom AsyncCachedValue store that calls _parsePreviousData() before determining whether it actually needs to update
      def getValue(self, *args, **kwargs):
        _bose._parsePreviousData()
        return super().getValue(*args, **kwargs)
      
    self._fbVersions  = {fb: BoseCachedValue[VersionMMP        ](lambda fb=fb: self._getFunctionBlockInfo(fb)) for fb in FB}
    self._bmapVersion      = BoseCachedValue[VersionMMP        ](self._getBmapVersion)
    self._volume           = BoseCachedValue[VolumeData        ](self._getVolume, invalidateAfter=0)
    self._firmwareVersion  = BoseCachedValue[VersionMMP        ](self._getFirmwareVersion)
    self._macAddress       = BoseCachedValue[MacAddress        ](self._getMacAddress, invalidateAfter=5*60)
    self._serialNumber     = BoseCachedValue[SerialNumber      ](self._getSerialNumber)
    self._hardwareRevision = BoseCachedValue[str               ](self._getHardwareRevision)
    self._productId        = BoseCachedValue[BoseProductId     ](self._getProductIdVariant)
    self._deviceName       = BoseCachedValue[DeviceName        ](self._getDeviceName, invalidateAfter=5*60)
    self._voicePrompts     = BoseCachedValue[VoicePromptSetting](self._getVoicePrompts, invalidateAfter=5*60)
    self._standbyTime      = BoseCachedValue[int               ](self._getStandbyTime, invalidateAfter=5*60)
    self._batteryLevel     = BoseCachedValue[int               ](self._getBatteryLevel, invalidateAfter=60)
    self._auxCablePresent  = BoseCachedValue[bool              ](self._getAuxCable, invalidateAfter=5)
    self._chargerPresent   = BoseCachedValue[bool              ](self._getChargerPresent, invalidateAfter=5)
    self._micLevel         = BoseCachedValue[int               ](self._getMicLevel, invalidateAfter=0.5)
    
    self._allStatus = _ValueList()

  # Mapping between commands and available parser functions
  
  _PARSERS = _ParserList()
  
  _ERRORS = {
    0x00: "Unknown (not used?)",
    0x01: "Invalid Length",
    0x02: "Invalid Checksum",
    0x03: "Function Block not supported",
    0x04: "Function not supported",
    0x05: "Operator not supported (for that function)",
    0x06: "Data values (sent to peripheral) are incorrect/malformed",
    0x07: "Requested Data is not available",
    0x08: "Failure to read/write the requested, temporary information",
    0x09: "Timeout Error",
    0x0a: "Requested Action is not applicable in current state",
    0x0b: "Device not paired to peripheral",
    0x0c: "Device is busy servicing the BMAP message",
    0x0d: "SoundLink device fails to connect to a device in the Paired Device List",
    0x0e: "SoundLink device fails to connect to a device because the pairing information has been deleted from the source device",
    0x0f: "OTA firmware update cannot be initialized because an update is already in progress",
    0x10: "OTA firmware update cannot be initialized because product battery voltage is too low",
    0x11: "OTA firmware update cannot be applied because charger is not connected",
    0xff: "Error code is Function Block specific and an extra byte will be included in the payload to differentiate between different Function Block specific error codes. Refer to the respective FBlock section for a list of error codes for that particular Function Block"
  }