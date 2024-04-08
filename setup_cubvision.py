import os
import sys

#Can't be bothered to do this stuff in shell dude

print("WiFi Connection May Be Needed!")

try:
    os.system("apt-get update")
    os.system("apt-get install gstreamer1.0")
    os.system("pip3 install -r requirements.txt")
except FileNotFoundError:
    pass

suffixes = [
    ["FL", "FR"],
    ["BL", "BR"],
    ["Sniper"]
]
ss = None
valid = False

suffix = input("Enter coprocessor suffix [FL, FR, Sniper, etc...] or suffix combination [FLFR, BLBR]: ")
if suffix != "Sniper":
    ss = [suffix[i:i+2] for i in range(0, len(suffix), 2)]
    for vs in suffixes:
        for s in ss:
            if s in vs:
                valid = True
    if not valid:
        print("Invalid coprocessor suffix")
        sys.exit(-1)
elif suffix == "Sniper":
    valid = True
    ss = [suffix]

runcommands = ""
for i in ss:
    runcommands += f"\npython3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/config{i}.json /home/orangepi/CubVision/calibration{i}.json &>> /home/orangepi/CubVision/log{i}.txt &\n"

base = open("launch_cubvision_base.sh", "r")
actual = open("launch_cubvision.sh", "w")

actual.write(base.read() + runcommands)

base.close()
actual.close()

os.system("cp /home/orangepi/CubVision/launch_cubvision.sh /etc/init.d")
os.system("chmod +x /etc/init.d/launch_cubvision.sh")
os.system("sed -i '13i sh /etc/init.d/launch_cubvision.sh' /etc/rc.local")
os.system("systemctl enable rc-local.service")

print("Installed CubVision")

