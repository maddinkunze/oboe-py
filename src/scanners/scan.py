import asyncio
try:
  import bleak
except ModuleNotFoundError:
  bleak = None
  
from .bose import BoseParser

from enum import Enum

class Parsers(Enum):
  BOSE = BoseParser

_default_scan_time = 10
_default_scan_parsers = {p for p in Parsers}

async def scan(time=_default_scan_time, parsers=_default_scan_parsers):
  stop_event = asyncio.Event()
  devices = []
  def callback(device, advertising_data):
    for parser in parsers:
      parsed_device = parser.value.parse(device, advertising_data)

      if not parsed_device:
        continue
      
      print(parsed_device.isInMusicShare)
      stop_event.set()

      devices.append(parsed_device)
      
  async with bleak.BleakScanner(callback):
    #await asyncio.sleep(time)
    await stop_event.wait()
  

def wait_for_scan(time=_default_scan_time, parsers=_default_scan_parsers):
  return asyncio.run(scan(time, parsers))
