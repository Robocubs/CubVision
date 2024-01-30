# CubVision

## What is CubVision?

Previously, our team used PhotonVision to track AprilTags for pose estimation. This worked
great, but eventually we realized we had a high demand for efficiency, speed, and accuracy during competitions which PhotonVision sometimes lacked. To improve autonomous, teleop, and every aspect of our game within, we developed CubVision.

## Northstar's cousin

Northstar is 6328's AprilTag tracking system using OpenCV's ArUco module and NT4. This code is provided for reference, but **6328 doesn't have the capacity to assist other teams in using it for custom setups**. Please check out [PhotonVision](https://photonvision.org) or [Limelight](https://limelightvision.io) as community-supported alternatives.

CubVision is a private fork of Northstar used by Team 1701 as the software for our vision coprocessors.

## Where does it run?

CubVision is meant to be a continuously-developed AprilTag tracking system for the future FRC games. During it's introduction in 2024, we used OrangePi 5's as our coprocessors. They provided great results at high speeds. However, it can be natively run on any machine which supports python to simulate and test robot or vision code.

| Machine     | Performance |
| ----------- | ----------- |
| OrangePi 5  | 90fps @ 8ms |
| M1 Air      | 120fps @ 3ms|
