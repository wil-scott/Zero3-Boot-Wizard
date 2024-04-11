"""
configdriver.py is responsible for running the Orange Pi Zero3 configuration program.
@author: Wil Scott
@date: April 2024
"""
import logging.config 
import logging.handlers
import argparse
import json
import pathlib
import shutil

from src.SetupManager import SetupManager
from src.MakeManager import MakeManager
from src.BlockDeviceManager import BlockDeviceManager
from src.FSManager import FSManager
from src.InstallManager import InstallManager
from src.Task import Task


class Driver(Task):
    def __init__(self):
        """
        Initialize instance of Driver.
        """
        self.logger = logging.getLogger("config_tool")

    def setup_logging(self):
        """
        Configures logger based on config.json file.
        
        :return: None
        """
        # Create logs directory if it doesn't exist
        log_dir = pathlib.Path("logs/")
        log_file = pathlib.Path("logs/zero3_config.log")
        if log_dir.exists() is False:
            pathlib.Path.mkdir(log_dir)
        if log_file.is_file() is False:
            pathlib.Path.touch(log_file)
        
        config_file = pathlib.Path("logging_config/config.json")
        with open(config_file) as file:
            config = json.load(file)
        logging.config.dictConfig(config)
        
        self.logger.info("Logger Configured.")

    def validate_args(self, args):
        """
        Validates command line arguments to ensure necessary information is present based on user's intent.

        :param args: an argparse object containing the parsed command line arguments.
        :return: True or None/Exit if valid flags present, else argparse.error is raised
        """
        if args.forceclean:
            try:
                shutil.rmtree(pathlib.Path("repositories"))
                self.logger.info("Repositories removed.")
            except Exception as e:
                self.logger.info("Error encountered when attempting to clean tool directory.")
                self.logger.error(e)
            exit()
        elif args.clean:
            commands = {
                1: ["sudo", "find", ".", "-maxdepth", "1", "-name", "wget-log*", "-delete"]
            }
            for key in commands.keys():
                if self.run_task(commands[key]) is False:
                    self.logger.debug(pathlib.Path.cwd())
                    self.logger.error("Error encountered while cleaning tool directory. Review log file for details.")
            exit()
        elif args.makeclean:
            # TODO: add subprocess commands for make-clean/make mrproper
            exit()
        elif args.blockdevice is None:
            self.logger.info("Missing Block Device argument detected.")
            raise argparse.ArgumentTypeError("Block device argument is required")
        else:
            return

    def log(self, message):
        """
        Log a message as info.

        :param message: a string representing the message to be logged
        :return: None
        """
        self.logger.info(message)

def main():
    """
    main() collects and parses command-line arguments necessary for running the config tool.
    """
    driver = Driver()
    # configure logging for the tool
    driver.setup_logging()
    
    # Parse commmand line arguments
    driver.log("Parsing command line args")
    parser = argparse.ArgumentParser(description="Configures a micro-SD card to run mainline Linux kernel on Orange Pi Zero3")
    parser.add_argument("-bd", "--blockdevice", type=str, help="Path to the block device representing the target Micro-SD Card")
    parser.add_argument("-d","--defconfig", default="opz3_defconfig", type=str, help="Name of defconfig file to be used for kernel configuration" )
    parser.add_argument("-fc", "--forceclean", action="store_true", help="Remove build and repositories directory")
    parser.add_argument("-c", "--clean", action="store_true", help="Remove the build directory and its contents")
    parser.add_argument("-mc", "--makeclean", action="store_true", help="Run 'make clean' in tf-a and u-boot repo. Run mrproper in 'linux' repo")
    args = parser.parse_args()
    driver.validate_args(args)

    # Instantiate Setup Helper and run config checking
    setup_helper = SetupManager(args.blockdevice, args.defconfig)
    if setup_helper.run_setup_manager() is False:
        driver.log("Unable to set up work environment. Please review logs for more information.")
        exit()
    
    driver.log("SetupManager has completed its tasks!") 
    
    # Make bl31 and u-boot
    make_manager = MakeManager(args.blockdevice, args.defconfig)
    if make_manager.run_uboot_make_commands() is False:
        driver.log("Unable to complete u-boot .bin compilation. Please review logs for more information.")
        exit()

    driver.log("MakeManager has finishing compiling u-boot.")

    # Format micro-sd card
    block_device_helper = BlockDeviceManager(args.blockdevice)
    if block_device_helper.configure_block_device_with_bootloader() is False:
        driver.log("Unable to configure block device. Please review logs for more information.")
        exit()

    driver.log(f"BlockDeviceManager has finished formatting {args.blockdevice}! U-boot is now on {args.blockdevice}.")

    # Make Image, dtb, modules
    if make_manager.run_linux_make_commands() is False:
        driver.log("Unable to complete linux make commands. Please review logs for more information.")
        exit()

    driver.log("MakeManager has finishing compiling Image, DTB, and modules.")

    # Make and configure RootFS
    fs_manager = FSManager(args.blockdevice)
    if fs_manager.configure_rootfs() is False:
        driver.log("Unable to configure RootFS. Please Review logs for more information.")
        exit()

    driver.log("FSManager has finished configuring the RootFS")

    # Install bootable files and modules onto block device
    install_manager = InstallManager(args.blockdevice)
    if install_manager.install_all() is False:
        driver.log("Unable to install bootable image files. Please Review logs for more information.")
        exit()

    driver.log("Install Manager has finished intalling boot files.")
    driver.log("Config Tool Successful! Exiting...")
    exit()

    #TODO: refactor classes to use generic subprocess class function 

if __name__ == "__main__":
    main()

