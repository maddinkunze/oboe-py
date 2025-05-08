# Oboe - A lbrary/program to communicate with bose devices



## Known Issues

### Windows

The scanner may return randomized addresses, even for peripherals that are bonded/paired to the computer (and could therefore be resolved by Windows but aren't for some reason). In those cases a connection will fail with differing errors. The only real known solution for now is to manually determine the real public mac address of your device within Windows settings/control panel (but good luck with that since control panel was "deprecated" while the settings don't show the mac address).