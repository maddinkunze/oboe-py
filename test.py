import src as oboe
import asyncio
import time

async def main():
  oboe.devices
  #d = oboe.devices.bose.BoseDevice("60:ab:d2:b0:bd:47")
  #await d.connect()
  #print(await d.getBmapVersion())
  #print(await d.getVolume())
  #print(await d.getSerialNumber())
  #print(await d.getMacAddress())
  #print((await d.getProductId()).getFullName())
  #print(await d.enableVoicePrompts())
  #print(await d.disableVoicePrompts())
  #print(await d.setLanguage((await d.getSupportedLanguages())[0]))
  #print(await d.getStandbyTime())
  #print(await d.getBatteryLevel())
  #print(await d.isAuxCableConnected())
  #print(await d.isChargerConnected())
  #print(await d._getMicLevel()) # TODO: someone should test this with headphones that support this function
  pass
  

asyncio.run(main())