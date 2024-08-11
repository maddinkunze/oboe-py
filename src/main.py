import time
from devices import bose
from devices.helpers import _bytesToHexString
from scanners.scan import wait_for_scan

def main():
  device = bose.BoseDevice("60:ab:d2:b0:bd:47") # Bose 35 II
  #device = bose.BoseDevice("4c:87:5d:09:61:16") # Powerheadset
  
  print(device.getBmapVersion())
  print(device.connectDeviceAndKeep("4c:87:5d:09:61:16", bose.BoseDevice.PairedDevice.ProductType.HEADPHONES, "84:5c:f3:9f:1a:ea"))
  #print(device.connectDeviceAndKeep("08:df:1f:48:58:3f", bose.BoseDevice.PairedDevice.ProductType.HEADPHONES, "84:5c:f3:9f:1a:ea"))
  time.sleep(1)
  print(_bytesToHexString(device.socket.recv(1000)))

if __name__ == "__main__":
  main()