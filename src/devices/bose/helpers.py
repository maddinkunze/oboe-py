import typing
from .types import CommandLike, Operator
if typing.TYPE_CHECKING:
  from . import BoseDevice

# a decorator that can be used to decorate parser functions, i.e.:
# when requesting to get the volume, the following call chain will occur:
# | -> getVolume()
# |   -> _getVolume()
# |     -> _sendCommandAndParseResponse()
# |       -> _sendCommand()
# |       -> _parseResponse()
# |         -> _parseVolume()
# for the _parseResponse function to know which parser-function is responsible when receiving a volume packet (i.e. _parseVolume() for _Audio_Function.VOLUME -> [0x05, 0x05])
# it has to have a map of all commands and respective parser-functions, which is what this decorator provides
# when decorating a function with this decorator, it will be saved in the BoseDevice._PARSERS list/map together with its respective command upon class creation and can then be later retrieved using self._PARSERS[<command>] (i.e. self._PARSERS[0x05, 0x05] = self._PARSERS[_Audio_Function.VOLUME] -> _parseVolume())
# the decorator can be used as follows (the actual implementation of _parseVolume() may be different):
# |  @parser(_Audio_Function.VOLUME)
# |  def _parseVolume(self, ..., *data):
# |    maxVolume, curVolume = data
# |    self._volume = curVolume
def parser(command: None|CommandLike|typing.Iterable[CommandLike|tuple[int, int|None]|tuple[None, int]], operator: None|Operator|typing.Iterable[Operator]=Operator.STATUS):
  class _parser_internal:
    def __init__(self, fn: typing.Callable):
      self._fn = fn
    def __call__(self):
      return self._fn
    def __set_name__(self, owner: typing.Type["BoseDevice"], *_):
      owner._PARSERS[command, operator] = self._fn
  return _parser_internal

def unknownResponse(fn: typing.Callable):
  def _fn(cls, *args, **kwargs):
    print("INFO: you just received a packet that could not be created by the projects author. if you would like to enhance the experience for other users, please open a github issue and include at least the following info:")
    print(f" - your title or description should contain something like \"reference packet {fn.__qualname__}()\"")
    print(" - your description should contain something like")
    if args:
      print("   <*args>")
    for i, arg in enumerate(args, 1):
      print(f"    [{i}] {arg}")
    if kwargs:
      print("   <**kwargs>")
    for n, arg in kwargs.items():
      print(f"    [{n}] {arg}")
    
    fn(cls, *args, **kwargs)
  return _fn