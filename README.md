# Orange Pi Zero3 Boot Wizard
This Python tool:
1. Creates all files necessary for a bootable image using the mainline Linux kernel
2. Configures a Micro-SD card with the partitions/files necessary to boot an Orange Pi Zero3 from a micro-SD card

The goal is to simplify the process for getting a bare-minimum image running on the Orange Pi Zero3 with as little fuss as possible. Altogether, the tool automates a ~1 hour long process.

## Requirements:
1. An Aarch64 Debian Linux System
2. Python3.11+
3. Internet connection
4. Micro-SD Card
5. Micro-SD Card reader of some kind (e.g. usb reader)

## How to Use:
1. Clone the tool's repository into your workspace
2. Optional: place your defconfig file in the `kernel_config` directory
2. Connect the Micro-SD card/Micro-SD card reader to your system
3. Determine the name associated with your Micro-SD card (e.g. run `lsblk` command)
4. In the repositories directory, run the tool via the command line. For example, `python3 main.py -bd /dev/sda` where your Micro-SD card is identified as `/dev/sda` on your system. If you are using your own defconfig file, include the `-d` flag (e.g. `-d name-of-your-defconfig`).

Note that for optimal performance you should run the script with sudo: `sudo python3 main.py -bd /dev/sda`. Without sudo privileges, the tool may hang at certain points while awaiting sudo/root password input.

The tool includes other flags that you can use as well. To see them, along with descriptions, run `python main.py -h` or `python main.py --help`.

## Known Issues:
1. Currently there is no way of selecting a branch/tag of the mainline linux kernel repository via the tool. This means that the tool will automatically use the latest version of the kernel. A workaround for this would be to manually clone the linux repo into the repositories directory and configure it as desired. 
