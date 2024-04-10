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


def setup_logging():
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

def validate_args(args, logger):
    """
    Validates command line arguments to ensure necessary information is present based on user's intent.

    :param args: an argparse object containing the parsed command line arguments.
    :return: True or None/Exit if valid flags present, else argparse.error is raised
    """
    if args.forceclean:
        try:
            shutil.rmtree(pathlib.Path("build"))
            shutil.rmtree(pathlib.Path("repositories"))
            logger.info("build and repositories removed.")
        except Exception as e:
            logger.info("Error encountered when attempting to clean tool directory.")
            logger.error(e)
        exit()
    elif args.clean:
        try:
            shutil.rmtree(pathlib.Path("build"))
            logger.info("build directory removed.")
        except Exception as e:
            logger.info("Error encountered when attempting to remove build directory.")
            logger.error(e)
        exit()
    elif args.makeclean:
        # TODO: add subprocess commands for make-clean/make mrproper
        exit()
    elif args.blockdevice is None:
        logger.info("Missing Block Device argument detected.")
        raise argparse.ArgumentTypeError("Block device argument is required")
    else:
        return

def main():
    """
    main() collects and parses command-line arguments necessary for running the config tool.
    """
    
    # configure logging for the tool
    logger = logging.getLogger("config_tool")
    setup_logging()
    logger.info("Logger configured")
    
    # Parse commmand line arguments
    logger.info("Parsing command line args")
    parser = argparse.ArgumentParser(description="Configures a micro-SD card to run mainline Linux kernel on Orange Pi Zero3")
    parser.add_argument("-bd", "--blockdevice", type=str, help="Path to the block device representing the target Micro-SD Card")
    parser.add_argument("-d","--defconfig", default="opz3_defconfig", type=str, help="Name of defconfig file to be used for kernel configuration" )
    parser.add_argument("-fc", "--forceclean", action="store_true", help="Remove build and repositories directory")
    parser.add_argument("-c", "--clean", action="store_true", help="Remove the build directory and its contents")
    parser.add_argument("-mc", "--makeclean", action="store_true", help="Run 'make clean' in tf-a and u-boot repo. Run mrproper in 'linux' repo")
    args = parser.parse_args()
    validate_args(args, logger)

    # Instantiate Setup Helper and run config checking
    setup_helper = SetupManager(args.blockdevice, args.defconfig)
    if setup_helper.run_setup_manager() is False:
        logger.info("Unable to set up work environment. Please review logs for more information.")
        exit()
    
    logger.info("SetupManager has completed its tasks!") 
    
    # Make bl31 and u-boot
    make_manager = MakeManager(args.blockdevice, args.defconfig)
    if make_manager.run_uboot_make_commands() is False:
        logger.info("Unable to complete u-boot .spl compilation. Please review logs for more information.")
        exit()

    logger.info("MakeManager has finishing compiling u-boot.")

    # Format micro-sd card
    block_device_helper = BlockDeviceManager(args.blockdevice)
    if block_device_helper.configure_block_device_with_bootloader() is False:
        logger.info("Unable to configure block device. Please review logs for more information.")
        exit()

    logger.info(f"BlockDeviceManager has finished formatting {args.blockdevice}! U-boot is now on {args.blockdevice}.")

    # Make Image, dtb, modules
    if make_manager.run_linux_make_commands() is False:
        logger.info("Unable to complete linux make commands. Please review logs for more information.")
        exit()

    logger.info("MakeManager has finishing compiling Image, DTB, and modules.")

    # Make and configure RootFS
    fs_manager = FSManager(args.blockdevice)
    if fs_manager.configure_rootfs() is False:
        logger.info("Unable to configure RootFS. Please Review logs for more information.")
        exit()

    logger.info("FSManager has finished configuring the RootFS")
    install_manager = InstallManager(args.blockdevice)
    if install_manager.install_all() is False:
        logger.info("Unable to install bootable image files. Please Review logs for more information.")
        exit()

    logger.info("Install Manager has finished intalling boot files.")
    logger.info("Config Tool Successful! Exiting...")
    exit()

    #TODO: finish general functionality for each class, complete successful runthrough of tool and test on OPZ3
    #TODO: refactor classes to use generic subprocess tool

if __name__ == "__main__":
    main()

