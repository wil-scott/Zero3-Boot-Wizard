"""
BlockDeviceManager is responsible for preping the user's block device to store the bootable image. 
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess

from src.Task import Task

class BlockDeviceManager(Task):

    def __init__(self, block_device):
        """
        Creates an instance of BlockDeviceManager.

        :param block_device: a string representing a micro-sd card to configure
        :return: None
        """
        self.logger = logging.getLogger("config_tool")
        self.block_device = block_device
        
        # define known file names
        self.spl_file = "repositories/u-boot/u-boot-sunxi-with-spl.bin"

        self.logger.info("BlockDeviceManager instantiated.")

    def _destroy_partition_table(self):
        """
        Overwrites traditional location of partition table on block device.

        :return: True if overwrite successful, else False
        """
        command_list = ["sudo", "dd", "if=/dev/zero", f"of={self.block_device}", "bs=1M", "count=1"]
        return self.run_task(command_list)
        
    def _write_spl_to_device(self):
        """
        Write .spl file created by u-boot + tf-a to block device.

        :return: True if write successful, else False
        """
        command_list = ["sudo", "dd", f"if={self.spl_file}", f"of={self.block_device}", "bs=1024", "seek=8"]
        return self.run_task(command_list)
        
    def mount_device(self):
        """
        Mount the block device to /mnt.

        :return: True if mount command successful, else False
        """
        command_list = ["sudo", "mount", self.block_device, "/mnt"]
        return self.run_task(command_list)
        
    def unmount_device(self):
        """
        Unmount the block device from /mnt.

        :return: True if unmount command successful, else False
        """
        command_list = ["sudo", "umount", "/mnt"]
        return self.run_task(command_list)
        
    def copy_file_to_mnt(self, source_path, destination_path=None):
        """
        Copy a file to the mounted device.

        :param source_path: the path of the file to be copied
        :param destination_path: the path of the destination for the file to be copied
        :return: True if copy was succesful, else False
        """
        command_list = ["sudo", "cp", "-r", source_path, destination_path]
        return self.run_task(command_list)
        
    def _create_new_partitions(self):
        """
        Create new partitions on block device.

        :return: True if block device configured successfully, else False
        """
        commands = {
            1: ["sudo", "blockdev", "--rereadpt", self.block_device],
            2: ["sudo", "sfdisk", self.block_device],
            3: ["sudo", "mkfs.vfat", f"{self.block_device}1"],
            4: ["sudo", "mkfs.ext4", f"{self.block_device}2"],
        }

        for key in commands.keys():
            if key == 2:
                cmd_input = "1M,64M,c\n,,L"
                cmd_text = True
            else:
                cmd_input = None
                cmd_text = None

            if self.run_task(commands[key], cmd_input=cmd_input, cmd_text=cmd_text) is False:
                return False

        return True

    def configure_block_device_with_bootloader(self):
        """
        Configures the block device to store the bootable image and write the bootloader to memory.

        :return: True if configuration is successful, else False
        """
        task_list = [
            self._destroy_partition_table,
            self._write_spl_to_device,
            self._create_new_partitions
        ]

        for task in task_list:
            if task() is False:
                return False

        return True

