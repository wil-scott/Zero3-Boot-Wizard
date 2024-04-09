"""
InstallManager is responsible for installing modules and copying bootable image files to boot partition.
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess

class InstallManager:

    def __init__(self, block_device):
        """
        Instantiates an object of type InstallManager.

        :param block_device: a String representing the user's Micro-SD Card
        """
        self.logger = logging.getLogger("config_tool")
        self.block_device = block_device
        self.arch = "ARCH=arm64"
        self.cross_comp = "CROSS_COMPILE=aarch64-linux-gnu-"
        self.module_path = "INSTALL_MOD_PATH=/mnt"
        self.header_path = "INSTALL_HDR_PATH=/mnt/usr/"

        self.logger.info("InstallManager Instantiated.")

    def mount_second_partition(self):
         """
        Mount the second partition on user's block device to /mnt/.

        :return: True if successful, else False
        """
        command_list = ["sudo", "mount", f"{self.block_device}2", "/mnt"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"{self.block_device}2 mounted at /mnt.")
        except subprocess.SubprocessError as e:
            self.logger.info(f"Unable to mount {self.block_device}2 at /mnt.")
            self.logger.error(e.stderr.decode())
            return False
        
        return True
    
    def _install_modules(self):
        """
        Mount the second partition on user's block device to /mnt/.

        :return: True if successful, else False
        """
        command_list = ["sudo", self.arch, self.cross_comp, self.module_path, "make", "modules", "modules_install"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Module installation command successful. Verifying modules present on RootFS...")
            if pathlib.Path("/mnt/lib/modules").is_dir() is False:
                self.logger.error("Modules not found at /mnt/lib/modules.")
                return False
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to install modules to RootFS.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _install_headers(self):
        """
        Attempts installation of Header files to RootFS. Copies files from linux/ to /mnt if necessary.

        :return: True if successful, else False
        """
        command_list_1 = ["sudo", self.arch, self.header_path, "make", "headers_install"]
        command_list_2 = ["sudo", "cp", "-r", "repositories/linux/usr/", "/mnt/usr/include/"]
        
        try:
            subprocess.run(command_list_1, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Header installation command complete.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to install header files.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    # Install Linux Firmware for RTL based chipsets
    def _install_firmware(self):
        """
        Copies RTL firmware to RootFS.

        :return: True if successful, else False
        """
        command_list = ["sudo", "cp", "-r", "repositories/linux-firmware/rtlwifi/", "/mnt/lib/firmware/"]
        try:
            subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Firmware install command successful. Verifying firmware present on RootFS...")
            if pathlib.Path("/mnt/lib/firmware/rtlwifi").is_dir() is False:
                self.logger.error("Firmware not ofund at /mnt/lib/firmware.")
                return False
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to install firmware.")
            self.logger.error(e.stderr.decode())
            return False

        return False

    def _switch_mounted_partition(self):
        """
        Unmount rootfs partition and mount boot partition.

        :return: True if successful, else False
        """
        command_list_1 = ["sudo", "umount", "/mnt"]
        command_list_2 = ["sudo", "mount", f"{self.block_device}1", "/mnt"]

    #

    # umount and mount first/boot partition

    # copy boot files/script

    # umount and eject
