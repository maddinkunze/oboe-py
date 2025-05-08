import typing
from ...libraries import asyncio
from ...helpers import CachedValue, ValueCollection
from ... import basetypes as bt


class AsyncDevice:
  async def connect(self) -> bool:
    raise NotImplementedError
  
  async def disconnect(self) -> bool:
    raise NotImplementedError
  
  async def isConnected(self) -> bool:
    raise NotImplementedError
  
  
  # Device Settings
  
  async def getDeviceName(self) -> str:
    raise NotImplementedError
  
  async def setDeviceName(self, name: str) -> str:
    raise NotImplementedError
  
  async def getNoiseCancellingMode(self):
    raise NotImplementedError
  
  async def setNoiseCancellingMode(self, mode):
    raise NotImplementedError
  
  async def getSupportedNoiseCancellingModes(self):
    raise NotImplementedError
  
  async def getVoicePassthroughMode(self):
    raise NotImplementedError
  
  async def setVoicePassthroughMode(self, mode):
    raise NotImplementedError
  
  async def getSupportedVoicePassthroughModes(self, mode):
    raise NotImplementedError
  
  async def startChirp(self):
    raise NotImplementedError
  
  async def stopChirp(self):
    raise NotImplementedError
  
  async def isChirping(self):
    raise NotImplementedError
  
  async def getButtonFunction(self):
    raise NotImplementedError
  
  async def setButtonFunction(self, button, function):
    raise NotImplementedError
  
  async def getSupportedButtons(self):
    raise NotImplementedError
  
  async def getSupportedButtonFunctions(self):
    raise NotImplementedError
  
  async def getLanguage(self):
    raise NotImplementedError
  
  async def setLanguage(self, language):
    raise NotImplementedError
  
  async def getSupportedLanguages(self):
    raise NotImplementedError
  
  async def isVoicePromptEnabled(self):
    raise NotImplementedError
  
  async def setVoicePromptEnabled(self, enabled):
    raise NotImplementedError
  
  async def enableVoicePrompts(self):
    return await self.setVoicePromptEnabled(True)
    
  async def disableVoicePrompts(self):
    return await self.setVoicePromptEnabled(False)
  
  async def getStandbyTime(self):
    raise NotImplementedError
  
  async def setStandbyTime(self, time):
    raise NotImplementedError
    
    
  # Runtime Infos
  
  async def getBatteryLevel(self):
    raise NotImplementedError
  
  async def isChargerConnected(self):
    raise NotImplementedError
  
  async def getVolume(self):
    raise NotImplementedError
  
  async def setVolume(self, volume):
    raise NotImplementedError
  
  async def getCurrentlyPlaying(self):
    raise NotImplementedError
  
  async def playSong(self):
    raise NotImplementedError
  
  async def pauseSong(self):
    raise NotImplementedError
  
  async def stopSong(self):
    raise NotImplementedError
  
  async def togglePlayPause(self):
    raise NotImplementedError
  
  async def nextSong(self):
    raise NotImplementedError
  
  async def previousSong(self):
    raise NotImplementedError
  
  async def isInPairingMode(self):
    raise NotImplementedError
  
  async def setPairingMode(self, enable):
    raise NotImplementedError
  
  
  # Connection Management
  
  async def listDevices(self):
    raise NotImplementedError
  
  async def getConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  async def disconnectConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  async def removeConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  async def removeAllConnectedDevices(self):
    raise NotImplementedError
  
  async def isAuxCableConnected(self):
    raise NotImplementedError
  
  
  # Music Share
  
  async def startMusicShare(self, withDevice):
    raise NotImplementedError
  
  async def stopMusicShare(self):
    raise NotImplementedError
  
  async def isInMusicShare(self):
    raise NotImplementedError
  
  async def getMusicShareStatus(self):
    raise NotImplementedError
  
  
  # Device Numbers
  
  async def getMacAddress(self) -> bt.DeviceAddress:
    raise NotImplementedError
  
  async def getSerialNumber(self) -> bt.SerialNumber:
    raise NotImplementedError
  
  async def getProductId(self) -> bt.ProductId:
    raise NotImplementedError
  
  async def getFirmwareVersion(self) -> bt.Version:
    raise NotImplementedError


class AsyncEventDevice(AsyncDevice):
  def __init__(self):
    self._event_task = None
    self._addToEventLoop()
  
  async def _eventLoopUpdate(self):
    raise NotImplementedError
  
  async def _eventLoop(self):
    while True:
      await self._eventLoopUpdate()
      await asyncio.sleep(0.001)
  
  def _addToEventLoop(self):
    self._event_task = asyncio.create_task(self._eventLoop())
  
  def _removeFromEventLoop(self):
    task = self._event_task
    self._event_task = None
    task.cancel()
    

class AsyncCachedValue[T](CachedValue[T]):
  def __init__(self, getterFunction: typing.Callable[[], typing.Coroutine[typing.Any, typing.Any, None]], setterFunction, *, initialValue: T|CachedValue._Sentinel = CachedValue._SENTINEL, invalidateAfter: int|float|None = None, invalidValue: T|CachedValue._Sentinel = CachedValue._SENTINEL, shouldUpdateOnFirstUse: bool = True):
    super().__init__(getterFunction, initialValue=initialValue, invalidateAfter=invalidateAfter, invalidValue=invalidValue, shouldUpdateImmediately=False, shouldUpdateOnFirstUse=shouldUpdateOnFirstUse)
    self._onSetEvents: list[asyncio.Event] = []
    self._orgLock = asyncio.Lock()
    self._valLock = asyncio.Lock()

  def addSingleOnChangeEvent(self):
    event = asyncio.Event()
    self._onSetEvents.append(event)
    return event
  
  def removeOnChangeEvent(self, event: asyncio.Event):
    try:
      self._onSetEvents.remove(event)
    except ValueError:
      pass

  @property
  def value(self) -> typing.Coroutine[typing.Any, typing.Any, T]:
    return super().value

  async def get(self, *, updateIfOutdated: bool = True, skipUpdate: bool = False) -> T:
    async with self._orgLock:
      async with self._valLock:
        shouldRefresh = (not skipUpdate) and self.shouldUpdate(updateIfOutdated=updateIfOutdated)
      if shouldRefresh:
        await self.functionToRefresh()
      async with self._valLock:
        return self._value
        
  async def set(self, value: T, *, countAsUpdate: bool = True):
    async with self._orgLock:
      pass
  
  async def _set(self, value: T, *, countAsUpdate: bool = True):
    async with self._valLock:
      pass
    

class AsyncValueCollection[K, V](ValueCollection[K, V]):
  def _initLocks(self):
    self._lock = asyncio.Lock()
    
  async def startCollecting(self):
    async with self._lock:
      self._startCollecting()
      
  async def stopCollectingAndMarkReadable(self):
    async with self._lock:
      self._stopCollecting()
      
  async def write(self, key: K, value: V):
    async with self._lock:
      self._write(key, value)
      
  async def read(self, key: K, default: V|None=None) -> V|None:
    async with self._lock:
      return self._read(key, default)
    
  async def copy(self) -> dict[K, V]:
    async with  self._lock:
      return self._copy()
        

#class AsyncPacketDevice[PT: Packet](AsyncEventDevice):
#  def __init__(self):
#    self._socket: socket.socket
#  def _connect(self):
#    pass
#  def _sendPacket(self, packet: PT):
#    self._socket.send(packet.toBytes())
#  def _recvPacket(self, untilFlag: Flag|None=None):
#    while True:
#      data = self._socket.recv()
#      # something data -> packet -> payload parser


# -> BD.getVolume()
#   -> BD._volume.get()
#     -> ACV._getter()
#       -> BD._sendCommand()

class AsyncBoseDevice(AsyncEventDevice):
  def __init__(self):
    self._c_allSettings = AsyncValueCollection[FunctionT, typing.Any]()
    self._volume = AsyncCachedValue(self._getVolume)
    self._allSettings = AsyncCachedValue(self._getAllSettings)
    
  async def getVolume(self):
    return await self._volume.get()
  
  
  # -> lambda-like
  async def _getVolume(self):
    flag = self._volume.addSingleOnChangeEvent()
    self._sendPacket(VolumePacket.createGetPacket())
    self._readEverythingIncoming(untilThisFlagIsSet=flag)
    
  # -> lambda-like (internal)
  async def _gotVolume(self, volume):
    self._volume.set(volume)
    self._c_allSettings.set(VolumePacket, volume)
    
  async def getAllSettings(self):
    return await self._settings.get()
  
  # -> lambda-like
  async def _getAllSettings(self):
    flag = self._allSettings.addSingleOnChangeEvent()
    self._c_allSettings.reset()
    self._sendPacket(AllSettingsPacket.createGetPacket())
    self._readEverythingIncomint(untilThisFlagIsSet=flag)
    
  # -> lambda-like
  async def _gotAllSettings(self):
    self._allSettings.set(self._c_allSettings)
    