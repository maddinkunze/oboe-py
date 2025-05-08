from ..libraries import _USE_ASYNCIO, _DEBUG_OR_TEST

from . import bose

from .base.syncdev import SyncDevice
if _USE_ASYNCIO:
  from .base.asyncdev import AsyncDevice
  
if _DEBUG_OR_TEST:
  Lol = 2