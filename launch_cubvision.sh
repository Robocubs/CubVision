#!/bin/sh

# !!! ONLY EXECUTE THIS SCRIPT DIRECTLY WHEN TESTING
# !!! IT SHOULD LAUNCH AUTOMATICALLY ON STARTUP

# Put commands here to launch one or more CubVision instances. This shell script is run at startup by /etc/rc.local
# /etc/rc.local should run this script. If it isn't, use `install_cubvision.sh`
# sudo systemctl status rc-local.service to check the status

python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/configFL.json /home/orangepi/CubVision/calibrationFL.json &>> /home/orangepi/CubVision/logFL.txt &
python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/configFR.json /home/orangepi/CubVision/calibrationFR.json &>> /home/orangepi/CubVision/logFR.txt &
