"""
configdriver.py is responsible for running the Orange Pi Zero3 configuration program.
@author: Wil Scott
@date: April 2024
"""
import atexit
import logging.config 
import logging.handlers
import argparse
import json
import pathlib
import shutil

from src.SetupManager import SetupManager


def setup_logging():
    """
    Configures logger based on config.json file.
    
    :return: None
    """
    
    config_file = pathlib.Path("logging_config/config.json")
    with open(config_file) as file:
        config = json.load(file)
    logging.config.dictConfig(config)

def validate_args(args):
    """
    Validates command line arguments to ensure necessary information is present based on user's intent.

    :param args: an argparse object containing the parsed command line arguments.
    :return: True or None/Exit if valid flags present, else argparse.error is raised
    """
    if args.clean:
        try:
            shutil.rmtree(pathlib.Path("build"))
            shutil.rmtree(pathlib.Path("build_repos"))
            logger.info("build and build_repos removed")
        except Exception as e:
            logger.info("Error encountered when attempting to clean tool directory.")
            logger.error(e)
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
    parser.add_argument("-d","--defconfig", type=str, help="Name of defconfig file to be used for kernel configuration" )
    parser.add_argument("-c", "--clean", action="store_true", help="Clean the tool's directory to a pre-configuration state")
    args = parser.parse_args()
    validate_args(args)
    exit()
    # Instantiate Setup Helper and run config checking
    setup_helper = SetupManager(args.blockdevice, args.config)
    
    # 
    
if __name__ == "__main__":
    main()

