# omxplayer-pir

A motion activated video player.

## Introduction

This python program has been written as an example for a [Motion activated video player 
(PIR sensor)](https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=121456).

When someone approaches the video player, a video is played. When that someone walks away,
the video is stopped.

A PIR (motion) sensor is used to control the playing of the video.

When the PIR sensor detects motion, the video is started to play. When the PIR sensor 
does no longer detects motion, the video is stopped.

The (single) video is played in a loop.

The program runs on a Raspberry Pi.

The program can be terminated with Ctrl+C.

Upon startup the program waits until the operator leaves the scene. Once the operator
has left the scene the fun starts.

## Details

### PIR (motion) sensor

The PIR sensor is connected to a GPIO.

The PIR sensor signals with
* a LOW signal that there is no motion detected,<br>
* a HIGH signal that motion has been detected.

### The video player (OMXPlayer)

The playing of the video is done with OMXPlayer.

When running OMXPlayer, it directly starts playing the video. OMXPlayer doesn't
have the ability to load (only) the video and start the (loaded) video with
a (play) command. 

However, OMXPlayer has a Pause command. This command pauses the video playing, and unpauses
(resumes) the paused video.

To overcome the load/play shortcoming, OMXPlayer is started and directly paused.

When motion is detected, the OMXPlayer is commanded to unpause the paused video.
When there is no motion detected anymore, OMXPlayer is commanded to pause the playing video.

### GPIO

The GPIO support is done with python module 'RPi.GPIO'.

## History
* V0.10 Initial version
* V0.11 Added video file exists check.
* V0.12 Changed 'the ẃaiting for PIR ready' into 'operator has left the scene'.
