# Automated Orange Pi Zero3 Bootable Image Tool
I know the title is a bit of a mouthful, but this Python tool:
1. Creates all files necessary for a bootable image using the mainline Linux kernel
2. Configures a Micro-SD card with the partitions/files necessary to boot an Orange Pi Zero3

The goal is to simplify the process for getting a bare-minimum image running on the Orange Pi Zero3 with as little fuss as possible.

## Requirements:
1. An Aarch64 Debian Linux System
2. Python3.11+
3. Internet connection
4. Micro-SD Card
5. Micro-SD Card reader of some kind (e.g. usb reader)

## How to Use:
1. Clone the repository
2. Connect the Micro-SD card/Micro-SD card reader to your system
3. Determine the name associated with your Micro-SD card (e.g. run `lsblk` command)
4. In the repositories directory, run the tool via the command line. For example, `python3 main.py -bd /dev/sda` where your Micro-SD card is identified as `/dev/sda` on your system. 

Note that for optimal performance you should run the script with sudo: `sudo python3 main.py -bd /dev/sda`. Without sudo privileges, the tool may hang at certain points while awaiting sudo/root password input.

The tool includes other flags that you can use as well. To see them, along with descriptions, run `python main.py -h` or `python main.py --help`.
