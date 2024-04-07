"""
FSmanager is responsible for bootstrapping the Debian RootFS onto the Micro-SD Card.
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess

class FSManager:

    def __init__(self, block_device):
        """
        Instantiates an object of type FSManager.

        :param block_device: a String representing the user's Micro-SD Card
        """
        self.logger = logging.getlogger("config_tool")
        self.block_device = block_device
        self.root_partition = f"{block_device}2"
        self.mount_dir = "/mnt/"
        self.debian_release = "bookworm" 
        self.chroot_command_list = ["sudo", "chroot", self.mount_dir, "/bin/sh", "-c"]

        self.logger.info("FSManager instantiated.")

     def mount_device(self):
        """
        Mount the root partition to /mnt.

        :return: True if mount command successful, else False
        """
        command_list = ["sudo", "mount", self.root_partition, "/mnt"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully mounted {self.root_partition} to /mnt.")
        except subproces.SubprocessError as e:
            self.logger.info("Failed to mount block device to /mnt.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def unmount_device(self):
        """
        Unmount the root partition from /mnt.

        :return: True if unmount command successful, else False
        """
        command_list = ["sudo", "umount", "/mnt"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully unmounted {self.root_partition} from /mnt.")
        except subproces.SubprocessError as e:
            self.logger.info("Failed to unmount block device from /mnt.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def bootstrap_stage_1(self):
        """
        Run stage 1 of debootstrap.

        :return: True if successful, else False
        """
        command_list = ["sudo", "debootstrap", "--arch=arm64", "--foreign", self.debian_release, self.mount_dir]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Debootstrap Stage 1 complete.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to complete Debootstrap Stage 1.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    #def enter_chroot(self):
        #"""
        #Run chroot command on mount directory.

        #:return: True if successful, else False
        #"""
        #command_list = ["sudo", "chroot", self.mount_dir, "/bin/sh", "-i"]
        #try:
            #subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #self.logger.info("Entered Chrooted /mnt environment.")
        #except subprocess.SubprocessError as e:
            #self.logger.info("Failed to enter Chrooted /mnt environment.")
            #self.logger.error(e.stderr.decode())
            #return False

        #return True

    def bootstrap_stage_2(self):
        """
        Run second stage of Debootstrap in chrooted /mnt.

        :return: True if successful, else False
        """
        command_list = ["/debootstrap/debootstrap", "--second-stage"]
        try:
            subprocess.run(self.chroot_command_list + command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Debootstrap Stage 2 complete.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to complete Debootstrap Stage 2.")
            self.logger.error(e.stderr.decode())
            self.logger.info("Attempting to exit Chroot")
            return False

        return True

    def run_chroot_command(self, command_list):
        """
        Run the command in a chrooted /mnt environment.

        :param command_list: a list containing the command args to be run in the chrooted environment
        :return: True if successful, else False
        """

    def configure_rootfs(self):
        """
        Configure bootstrapped RootFS.

        :return: True if successful, else False
        """

