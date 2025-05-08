from .types import BmapPacket
from .packets import FunctionBlocks
from ...helpers import bytesToHexString

ERRORS_GENERAL = {
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

ERRORS_FB_SPECIFIC = {
  FunctionBlocks.DeviceManagement.BYTE: {
    0x00: "Unsupported Connection Type (Master)",
    0x01: "Unsupported Connection Type (Puppet)",
    0x02: "Incompatible Puppet needs Update",
    0x03: "Incompatible Master needs Update"
  }
}

ERROR_NO_ERROR = "Unknown Error (no error message could be found/extracted)"
ERROR_UNEXPECTED_LENGTH = "The error packet does not have the expected length (expected: {exp}, got: {got})"
ERROR_NO_FUNCTION_BLOCKS = "There are no specific errors registered for this function block"
ERROR_NO_FB_ERROR = "Unknown FB Error (no error message could be found within the specific error messages of this function block)"

def getErrorMessageFromBytes(packet: BmapPacket):
  headerBytes = bytesToHexString(packet.header)
  data = packet.payload
  errBytes = bytesToHexString(data)
  errors = []

  l = len(data)
  b1 = None
  if l < 1:
    errors.append(ERROR_UNEXPECTED_LENGTH.format(exp="1-2", got=l))
  else:
    b1 = data[0]    
    
  errors.append(ERRORS_GENERAL.get(b1, ERROR_NO_ERROR))
  
  if b1 == 0xff:
    b2 = None
    if l == 2:
      b2 = data[1]
    else:
      errors.append(ERROR_UNEXPECTED_LENGTH.format(exp="2", got=l))
      
    fb = packet.function.FUNCTION_BLOCK.BYTE
    fb_errors = ERRORS_FB_SPECIFIC.get(fb, None)
    if fb_errors is None:
      errors.append(ERROR_NO_FUNCTION_BLOCKS)
    else:
      errors.append(fb_errors.get(b2, ERROR_NO_FB_ERROR))
  elif l > 1:
    errors.append(ERROR_UNEXPECTED_LENGTH.format(exp="1", got=l))
    
  multipleErrorsS = ""
  multipleErrorsNL = " "
  if len(errors) > 1:
    multipleErrorsS = "s"
    multipleErrorsNL = "\n"
  
  return f"The following error{multipleErrorsS} occurred [{headerBytes} -> {errBytes}]:{multipleErrorsNL}{multipleErrorsNL.join(errors)}"
