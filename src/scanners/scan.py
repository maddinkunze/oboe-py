import typing
from ..libraries import asyncio, bleak
from .base import Parser

from .bose import BoseParser

from enum import Enum

class Parsers(Enum):
  def __init__(self, *args, **kwargs):
    self.value: typing.Type[Parser]
    super().__init__(*args, **kwargs)
    
  BOSE = BoseParser


_DEFAULT_SCAN_TIME = 10
_DEFAULT_SCAN_PARSERS: set[Parsers] = {p for p in Parsers}

async def scan(time=_DEFAULT_SCAN_TIME, parsers: typing.Iterable[Parsers]=_DEFAULT_SCAN_PARSERS):
  stop_event = asyncio.Event()
  
  devices = {}
  def callback(device, advertising_data):
    macAddr = device.address
    
    for parser in parsers:
      existing = devices.get(macAddr, None)
      parsed_device = parser.value.parse(device, advertising_data, existing)

      if not parsed_device:
        continue

      devices[macAddr] = (parsed_device, device)
      
  async with bleak.BleakScanner(callback):
    await asyncio.sleep(time)
    #await stop_event.wait()
    
  return devices
  

def wait_for_scan(time=_DEFAULT_SCAN_TIME, parsers=_DEFAULT_SCAN_PARSERS):
  return asyncio.run(scan(time, parsers))
