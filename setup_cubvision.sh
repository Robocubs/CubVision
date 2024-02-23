#!/bin/sh

echo "This script needs work"
exit 0

# SHOULD BE RUN ON VISION MACHINE

echo "WiFi Connection May Be Needed!"

# COMMENT THESE 3 LINES IF NO WIFI CONNECTION
apt-get update
apt-get install gstreamer1.0
pip3 install -r requirements.txt

echo "Enter coprocessor suffix [FL, FR, Sniper, etc...] or suffix combination [FLFR, BLBR]:"
read SUFFIX
string='FLFRBLBRSniper'
if [[ $string != *$SUFFIX* ]]; then
    echo "Invalid coprocessor suffix"
    exit 1
fi

n=${#SUFFIX}
RUNCOMMAND=""
SINGLECOMMAND="python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/config${SUFFIX}.json /home/orangepi/CubVision/calibration${SUFFIX}.json &>> /home/orangepi/CubVision/log${SUFFIX}.txt &"

if [ "$n" -eq "4" ]; then
    SPLIT1=${SUFFIX:0:2}
    SPLIT2=${SUFFIX:2:2}
    RUNCOMMAND="""python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/config${SPLIT1}.json /home/orangepi/CubVision/calibration${SPLIT1}.json &>> /home/orangepi/CubVision/log${SPLIT1}.txt &
python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/config${SPLIT2}.json /home/orangepi/CubVision/calibration${SPLIT2}.json &>> /home/orangepi/CubVision/log${SPLIT2}.txt &"""
elif [ "$n" -eq "2" ]; then
    RUNCOMMAND=$SINGLECOMMAND
elif [ "$n" -eq "6" ]; then
    RUNCOMMAND=$SINGLECOMMAND
else
    echo "Invalid coprocessor suffix"
    exit 1
fi

sed -i.bak -e '10,12d' launch_cubvision.sh
sed -i  -e "10i\\$RUNCOMMAND" launch_cubvision.sh

sudo cp /home/orangepi/CubVision/launch_cubvision.sh /etc/init.d
sudo chmod +x /etc/init.d/launch_cubvision.sh

OUTPUT=$(cat /etc/rc.local | grep "launch_cubvision.sh")
if [ "$OUTPUT" != "" ]; then
    echo "Already installed CubVision"
    exit 0
fi

sed -i '13i sh /etc/init.d/launch_cubvision.sh' /etc/rc.local
sudo systemctl enable rc-local.service
echo "Installed CubVision"