#!/bin/sh

# SHOULD BE RUN ON VISION MACHINE

echo "WiFi Connection May Be Needed!"

pip3 install -r requirements.txt
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