from ...libraries import threading, eventloop
from ... import basetypes as bt


class SyncDevice:
  def connect(self) -> bool:
    raise NotImplementedError
  
  def disconnect(self) -> bool:
    raise NotImplementedError
  
  def isConnected(self) -> bool:
    raise NotImplementedError
  
  
  # Device Settings
  
  def getDeviceName(self) -> str:
    raise NotImplementedError
  
  def setDeviceName(self, name: str) -> str:
    raise NotImplementedError
  
  def getNoiseCancellingMode(self):
    raise NotImplementedError
  
  def setNoiseCancellingMode(self, mode):
    raise NotImplementedError
  
  def getSupportedNoiseCancellingModes(self):
    raise NotImplementedError
  
  def getVoicePassthroughMode(self):
    raise NotImplementedError
  
  def setVoicePassthroughMode(self, mode):
    raise NotImplementedError
  
  def getSupportedVoicePassthroughModes(self, mode):
    raise NotImplementedError
  
  def startChirp(self):
    raise NotImplementedError
  
  def stopChirp(self):
    raise NotImplementedError
  
  def isChirping(self):
    raise NotImplementedError
  
  def getButtonFunction(self):
    raise NotImplementedError
  
  def setButtonFunction(self, button, function):
    raise NotImplementedError
  
  def getSupportedButtons(self):
    raise NotImplementedError
  
  def getSupportedButtonFunctions(self):
    raise NotImplementedError
  
  def getLanguage(self):
    raise NotImplementedError
  
  def setLanguage(self, language):
    raise NotImplementedError
  
  def getSupportedLanguages(self):
    raise NotImplementedError
  
  def isVoicePromptEnabled(self):
    raise NotImplementedError
  
  def setVoicePromptEnabled(self, enabled):
    raise NotImplementedError
  
  def enableVoicePrompts(self):
    return self.setVoicePromptEnabled(True)
    
  def disableVoicePrompts(self):
    return self.setVoicePromptEnabled(False)
  
  def getStandbyTime(self):
    raise NotImplementedError
  
  def setStandbyTime(self, time):
    raise NotImplementedError
    
    
  # Runtime Infos
  
  def getBatteryLevel(self):
    raise NotImplementedError
  
  def isChargerConnected(self):
    raise NotImplementedError
  
  def getVolume(self):
    raise NotImplementedError
  
  def setVolume(self, volume):
    raise NotImplementedError
  
  def getCurrentlyPlaying(self):
    raise NotImplementedError
  
  def playSong(self):
    raise NotImplementedError
  
  def pauseSong(self):
    raise NotImplementedError
  
  def stopSong(self):
    raise NotImplementedError
  
  def togglePlayPause(self):
    raise NotImplementedError
  
  def nextSong(self):
    raise NotImplementedError
  
  def previousSong(self):
    raise NotImplementedError
  
  def isInPairingMode(self):
    raise NotImplementedError
  
  def setPairingMode(self, enable):
    raise NotImplementedError
  
  
  # Connection Management
  
  def listDevices(self):
    raise NotImplementedError
  
  def getConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  def disconnectConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  def removeConnectedDevice(self, deviceId):
    raise NotImplementedError
  
  def removeAllConnectedDevices(self):
    raise NotImplementedError
  
  def isAuxCableConnected(self):
    raise NotImplementedError
  
  
  # Music Share
  
  def startMusicShare(self, withDevice):
    raise NotImplementedError
  
  def stopMusicShare(self):
    raise NotImplementedError
  
  def isInMusicShare(self):
    raise NotImplementedError
  
  def getMusicShareStatus(self):
    raise NotImplementedError
  
  
  # Device Numbers
  
  def getMacAddress(self) -> bt.DeviceAddress:
    raise NotImplementedError
  
  def getSerialNumber(self) -> bt.SerialNumber:
    raise NotImplementedError
  
  def getProductId(self) -> bt.ProductId:
    raise NotImplementedError
  
  def getFirmwareVersion(self) -> bt.Version:
    raise NotImplementedError
  
  
class SyncEventDevice(SyncDevice):
  def __init__(self):
    self._addToEventLoop()
  
  def _eventLoopUpdate(self):
    raise NotImplementedError
  
  def _addToEventLoop(self):
    if not eventloop:
      return
    eventloop.addCallback(self._eventLoopUpdate)
  
  def _removeFromEventLoop(self):
    if not eventloop:
      return
    eventloop.removeCallback(self._eventLoopUpdate)
