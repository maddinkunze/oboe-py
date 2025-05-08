import sys
import oboe
import time
import argparse

PROG_NAME = "Oboe"
PROG_VER = "0.1.0"
PROG_DESC = "A command line interface to communicate with wireless bluetooth devices (headphones). Currently only certain devices from Bose are supported"
PROG_NAME_VER = f"{PROG_NAME} ({PROG_VER})"

DEVICE_CLASSES = {
  "bose": oboe.devices.bose.BoseDevice,
  "b": oboe.devices.bose.BoseDevice,
}
PARSER_CLASSES = {
  "bose": oboe.scanners.Parsers.BOSE,
  "b": oboe.scanners.Parsers.BOSE,
}
ANS_ALL = ["all", "a"]
ANS_YES = ["yes", "y"]
ANS_NO = ["no", "n"]
ANS_YES_NO = [*ANS_YES, *ANS_NO]
ANS_ALL_YES_NO = [*ANS_ALL, *ANS_YES_NO]
DEVICE_COMMAND_SEP = "+"

def main():
  parser = argparse.ArgumentParser(prog=PROG_NAME_VER, description=PROG_DESC)
  subparsers = parser.add_subparsers(required=True)
    
  parser_list = subparsers.add_parser("list", aliases=["l"], help="Scan for possibly supported devices")
  add_args_list(parser_list)
  parser_list.set_defaults(m1_func=parse_args_list)
  
  parser_device = subparsers.add_parser("device", aliases=["d"], help="Perform actions on a device")
  add_args_device(parser_device)
  parser_device.set_defaults(m1_func=parse_args_device)
  
  args, ukargs = parser.parse_known_args()
  print(args)
  args.m1_func(args, ukargs)

##########
#  LIST  #
##########
def add_args_list(parser):
  parser.add_argument("-p", "--parsers", nargs="*", choices=[*ANS_ALL, *PARSER_CLASSES], default="all")
  parser.add_argument("-t", "--timeout", type=int, default="10")
  parser.add_argument("-f", "--format", choices=["mac+name", "mac", "raw", "pipe"], default="mac+name")
  parser.add_argument("-l", "--limit", type=int, default="-1", help="Stops the search before the timeout is reached, as soon as the specified amount of devices are found")
  parser.add_argument("-b", "--bonded", "--paired", nargs="?", choices=ANS_YES_NO, const="y", default="all", help="Filter devices by whether or not they are paired",  dest="paired")
  parser.add_argument("-c", "--connected", nargs="?", choices=ANS_YES_NO, const="y", default="all", help="Filter devices by whether or not they are currently connected")
  
def parse_args_list(args, ukargs):
  parse_remaining_args(ukargs)
  devices = oboe.wait_for_scan(args.timeout)
  for mac, device in devices.items():
    print(f"{mac} - {device.name}")
  

############
#  DEVICE  #
############
def add_args_device(parser):
  if sys.stdin.isatty():
    parser.add_argument("type", choices=[*DEVICE_CLASSES], help="Type of device")
    parser.add_argument("address", help="MAC address of the device")
  else:
    data = sys.stdin.read().strip().split(" ")
    parser.set_defaults(dev_type=data[0])
    parser.set_defaults(address=data[1])
  
  parser.add_argument("-nc", "--no-connect", action="store_true", help="Do not connect to device, only use this if you are sure you do not need to connect to the device to perform the action (rare)")

def parse_args_device(args, ukargs):
  try:
    device = DEVICE_CLASSES[args.type](args.address)
    if not args.no_connect:
      device.connect()
  except:
    if sys.platform == "win32":
      print("[WARNING] If you used the scanner to determine the mac address, the following error may be because windows returns a randomized mac address instead of the actual mac address. Please determine the real public mac address of your device in settings or similar and try again.")
      time.sleep(2)
    raise
    
  parse_args_device_commands(ukargs, device)

def add_args_device_command(parser):
  subparsers = parser.add_subparsers(required=True)
  
  parser_volume = subparsers.add_parser("volume", aliases=["v"], help="Get or set volume of the peripheral")
  parser_volume.set_defaults(dc1_func=print)
  
  parser_music_share = subparsers.add_parser("musicshare", aliases=["mshare", "ms"], help="Start/Stop music share or get current music share status")
  parser_music_share.set_defaults(dc1_func=print)

def parse_args_device_commands(args, device):
  args_split = []
  last_split = 0
  for i, arg in enumerate(args):
    if arg.strip() != DEVICE_COMMAND_SEP:
      continue
    args_split.append(args[last_split:i])
    last_split = i + 1
  args_split.append(args[last_split:])
  
  parser = argparse.ArgumentParser(prog=PROG_NAME_VER, description=PROG_DESC)
  add_args_device_command(parser)
  
  for args_sub in args_split:
    if not args_sub:
      continue
    
    args_parsed = parser.parse_args(args_sub)
    args_parsed.dc1_func(args_parsed)
  
#############
#  HELPERS  #
#############
def is_all(answer):
  return answer in ANS_ALL

def is_yes(answer):
  return answer in ANS_YES

def is_no(answer):
  return answer in ANS_NO

def parse_remaining_args(args):
  argparse.ArgumentParser(prog=PROG_NAME_VER, description=PROG_DESC).parse_args(args)
  
if __name__ == "__main__":
  main()