# CubVision

## What is CubVision?

Previously, our team used PhotonVision to track AprilTags for pose estimation. This worked
great, but eventually we realized we had a high demand for efficiency, speed, and accuracy during competitions which PhotonVision sometimes lacked. To improve autonomous, teleop, and every aspect of our game within, we developed CubVision.

## Northstar's cousin

Northstar is 6328's AprilTag tracking system using OpenCV's ArUco module and NT4. This code is provided for reference, but **6328 doesn't have the capacity to assist other teams in using it for custom setups**. Please check out [PhotonVision](https://photonvision.org) or [Limelight](https://limelightvision.io) as community-supported alternatives.

CubVision is a private fork of Northstar used by Team 1701 as the software for our vision coprocessors.

## Where does it run?

CubVision is meant to be a continuously-developed AprilTag tracking system for the future FRC games. During its introduction in 2024, we used OrangePi 5's as our coprocessors. They provided great results at high speeds. However, it can natively run on any machine which supports python to simulate and test robot or vision code.

| Machine     | Performance | OpenCV Build Time |
| ----------- | ----------- | ----------------- |
| OrangePi 5  | 90fps @ 8ms | > 35 minutes      |
| M1 Air      | 120fps @ 3ms| ~ 20 minutes      |

## How do I install it on a coprocessor?

**STOP:** If you are unaware of what you're doing, or what you're running, get someone who does to help you. The build and installation of the required OpenCV build requires careful attention.

*NOTE:* A pre-packaged and built OpenCV is located in the `Releases` page on this repository. Head there and download if you don't want to rebuild OpenCV (which takes awhile).

> *Ensure Docker is installed*

> For MacOS, Linux **ONLY**
1. If you need to rebuild OpenCV, head to the `docker` directory in the repository
2. run `sh build_opencv.sh`. This will build and copy the `cv` package and the OpenCV shared libraries in `lib` to the `docker` directory.
3. Use the commented `scp` commands located at the bottom of the `build_opencv.sh` to copy the directories over to a remote machine. TODO: Fix the issue with overwriting non .so's (see `build_opencv.sh`)

> Windows

I have not tried Windows, but Docker does support it. You can run the image and get OpenCV built with ease, but the shell script may not work on command lines that are ported to Windows (like Git Bash). Advance **ONLY** if you know what you're doing!

To fully install, copy the `CubVision` repo over to the coprocessor and change your directory to `CubVision`. Open and edit the `launch_cubvision.sh` script to match the commands for `CubVision` for a specific coprocessor (e.g. running the front-right camera). Run the `install_cubvision.sh` shell script after you edit the `launch_cubvision.sh` script. This should point the coprocessor to execute the `launch_cubvision.sh` script on startup.