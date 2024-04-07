"""
BlockDeviceManager is responsible for preping the user's block device to store the bootable image. 
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess


class BlockDeviceManager:

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
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"dd command complete - partition wiped from {self.block_device}.")
        except subprocess.SubprocessError as e:
            self.logger.info("dd command to wipe partition failed.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _write_spl_to_device(self):
        """
        Write .spl file created by u-boot + tf-a to block device.

        :return: True if write successful, else False
        """
        command_list = ["sudo", "dd", f"if={self.spl_file}", f"of={self.block_device}", "bs=1024", "seek=8"]
        
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f".spl successfully written to {self.block_device}.")
        except subprocess.SubprocessError as e:
            self.logger.info("dd command to write .spl to block device failed.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def mount_device(self):
        """
        Mount the block device to /mnt.

        :return: True if mount command successful, else False
        """
        command_list = ["sudo", "mount", self.block_device, "/mnt"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully mounted {self.block_device} to /mnt.")
        except subproces.SubprocessError as e:
            self.logger.info("Failed to mount block device to /mnt.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def unmount_device(self):
        """
        Unmount the block device from /mnt.

        :return: True if unmount command successful, else False
        """
        command_list = ["sudo", "umount", "/mnt"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully unmounted {self.block_device} from /mnt.")
        except subproces.SubprocessError as e:
            self.logger.info("Failed to unmount block device from /mnt.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def copy_file_to_mnt(self, source_path, destination_path=None):
        """
        Copy a file to the mounted device.

        :param source_path: the path of the file to be copied
        :param destination_path: the path of the destination for the file to be copied
        :return: True if copy was succesful, else False
        """

        command_list = ["sudo", "cp", "-r", source_path, destination_path]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully copied {source_path} to {destination_path}")
        except subprocess.SubprocessError as e:
            self.logger.info(f"Failed to copy {source_path} to {destination_path}")
            self.logger.error(e.stderr.decode())
            return False
        
        return True

    def _create_new_partitions(self):
        """
        Create new partitions on block device.

        :return: True if block device configured successfully, else False
        """
        command_list_1 = ["sudo", "blockdev", "--rereadpt", self.block_device] 
        command_list_2 = ["sudo", "sfdisk", self.block_device]
        command_list_3 = ["sudo", "mkfs.vfat", f"{self.block_device}1"]
        command_list_4 = ["sudo", "mkfs.ext4", f"{self.block_device}2"]
        command_2_input = "1M,64M,c\n,,L"

        try:
            subprocess.run(command_list_1, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully updated kernel view of partition table.")
            subprocess.run(command_list_2, input=command_2_input, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully partitioned {self.block_device}")
            subprocess.run(command_list_3, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(command_list_4, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully formatted partitions on {self.block_device}")
        except subprocess.SubprocessError as e:
            self.logger.info(f"Error while partitioning {self.block_device}")
            self.logger.error(e.stderr.decode())
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

