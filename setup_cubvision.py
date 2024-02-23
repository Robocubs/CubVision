import subprocess
import sys

#Can't be bothered to do this stuff in shell dude
#TODO: Super messy script, but it works and I clean it up later.

print("This script needs work")
sys.exit(1)

print("WiFi Connection May Be Needed!")


try:
    subprocess.run(["apt-get", "update"]) 
    subprocess.run(["apt-get", "install", "gstreamer1.0"])
    subprocess.run(["pip3 install", "-r", "requirements.txt"])
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

runcommands = []
for i in ss:
    runcommands.append(f"python3 /home/orangepi/CubVision/main.py /home/orangepi/CubVision/config{i}.json /home/orangepi/CubVision/calibration{i}.json &>> /home/orangepi/CubVision/log{i}.txt &\n")

open("launch_cubvision.sh", "w").close()
with open("launch_cubvision.sh", "w+") as f:
    lines = f.readlines()
    f.truncate()
    for i in range(10, len(runcommands)):
        lines[i] = runcommands[i]
    f.writelines(lines)


