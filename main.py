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


def setup_logging():
    config_file = pathlib.Path("logging_config/config.json")
    with open(config_file) as file:
        config = json.load(file)
    logging.config.dictConfig(config)


def main():
    """
    main() collects and parses command-line arguments necessary for running the config tool.
    """
    
    # configure logging for the tool
    logger = logging.getLogger()
    setup_logging()
    logger.info("Logger configured")

    logger.info("Parsing command line args")
    parser = argparse.ArgumentParser(description="Configures a micro-SD card to run mainline Linux kernel on Orange Pi Zero3")
    parser.add_argument("-bd", "--blockdevice", type=str, required=True, help="Path to the block device representing the target Micro-SD Card")
    parser.add_argument("-c","--config", type=str, required=True, help="Name of defconfig file to be used for kernel configuration" )
    args = parser.parse_args()


if __name__ == "__main__":
    main()

