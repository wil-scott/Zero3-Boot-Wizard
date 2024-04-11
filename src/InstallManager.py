"""
InstallManager is responsible for installing modules and copying bootable image files to boot partition.
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess
from src.Task import Task

class InstallManager(Task):

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

    def _mount_second_partition(self):
        """
        Mount the second partition on user's block device to /mnt/.

        :return: True if successful, else False
        """
        command_list = ["sudo", "mount", f"{self.block_device}2", "/mnt"]
        return self.run_task(command_list)

    def _install_modules(self):
        """
        Mount the second partition on user's block device to /mnt/.

        :return: True if successful, else False
        """
        repo_dir = "repositories/linux"
        command_list = ["sudo", self.arch, self.cross_comp, self.module_path, "make", "modules", "modules_install"]
        result = self.run_task(command_list, cmd_cwd=repo_dir)
        if result and pathlib.Path("/mnt/lib/modules").is_dir():
            return True 
        else:
            self.logger.info("Unable to install modules to RootFS.")
            return False

    def _install_headers(self):
        """
        Attempts installation of Header files to RootFS. Copies files from linux/ to /mnt if necessary.

        :return: True if successful, else False
        """
        repo_dir = "repositories/linux"
        commands = {
            1: ["sudo", self.arch, self.header_path, "make", "headers_install"],
            2: ["sudo", "cp", "-r", "usr/include", "/mnt/usr/include/"]
        }

        for key in commands.keys():
            if self.run_task(commands[key], cmd_cwd=repo_dir) is False:
                return False
        return True

    def _install_firmware(self):
        """
        Copies RTL firmware to RootFS.

        :return: True if successful, else False
        """
        command_list = ["sudo", "cp", "-r", "repositories/linux-firmware/rtlwifi/", "/mnt/lib/firmware/"]
        result = self.run_task(command_list)
        
        if result and pathlib.Path("/mnt/lib/firmware/rtlwifi").is_dir():
            return True        
        else:
            self.logger.info("Unable to install firmware.")
            return False

    def _post_kernel_header_clean(self):
        """
        Remove unnecessary byproducts of make deb-pkg recipe.

        :return: True if successful, else False
        """
        working_dir = "repositories"
        commands = {
            1: ["sudo", "rm", "-fr", "linux-image*"],
            2: ["sudo", "rm", "-fr", "linux-libc*"],
            3: ["sudo", "rm", "-fr", "linux-upstream*"],
            4: ["sudo", "rm", "-fr", "linux-headers*"]
        }
        for key in commands.keys():
            if self.run_task(" ".join(commands[key]), cmd_cwd=working_dir, use_shell=True) is False:
                return False
        return True
    
    def _create_kernel_headers(self):
        """
        Create linux/kernel header files.

        :return: True if successful, else False
        """
        command_list = ["sudo", "make", "deb-pkg"]
        repo_dir = "repositories/linux"
        return self.run_task(command_list, cmd_cwd=repo_dir)

    def _copy_kernel_headers(self):
        """
        Copy linux kernel headers to /mnt/usr/src.

        :return: True if successful, else False
        """
        command_list = ["sudo", "cp", "-r", "debian/linux-headers-*/usr/src/*", "/mnt/usr/src/"]
        repo_dir = "repositories/linux"
        return self.run_task(" ".join(command_list), cmd_cwd=repo_dir, use_shell=True)  # Shell required to expand wildcard

    def _switch_mounted_partition(self):
        """
        Unmount rootfs partition and mount boot partition.

        :return: True if successful, else False
        """
        commands = {
            1: ["sudo", "umount", "/mnt"],
            2: ["sudo", "mount", f"{self.block_device}1", "/mnt"]
        }
       
        for key in commands.keys():
            if self.run_task(commands[key]) is False:
                return False
        return True

    def _copy_boot_files(self):
        """
        Copy Image, dtb, dtbo, and boot script to boot partition.

        :return: True if successful, else False
        """
        commands = {
            1: ["sudo", "cp", "-r", "repositories/linux/arch/arm64/boot/Image", "/mnt"],
            2: ["sudo", "cp", "-r", "repositories/linux/arch/arm64/boot/dts/allwinner/sun50i-h618-orangepi-zero3.dtb", "/mnt/device_tree.dtb"],
            3: ["sudo", "cp", "-r", "kernel_config/boot.scr", "/mnt"],
            4: ["sudo", "cp", "-r", "kernel_config/expansion-board-overlay.dtbo", "/mnt"],
        }
        required_boot_files = {"Image", "device_tree.dtb", "boot.scr", "expansion-board-overlay.dtbo"}

        for key in commands.keys():
            if self.run_task(commands[key]) is False:
                return False

        # Perform final check that boot files are present in boot partition
        mnt_contents = set(obj.name for obj in pathlib.Path("/mnt").iterdir())
        if required_boot_files != mnt_contents:
            self.logger.error("Unable to verify boot partition contents.")
            return False
        else:
            return True

    def _unmount_device(self):
        """
        Unmount the boot partition.

        :return: True if successful, else False
        """
        command_list = ["sudo", "umount", "/mnt"]
        return self.run_task(command_list)

    def install_all(self):
        """
        Install/Copy necessary files to root and boot partitions.

        :return: True if successful, else False
        """
        task_list = [
            self._mount_second_partition,
            self._install_modules, 
            self._install_headers,
            self._install_firmware,
            self._create_kernel_headers,
            self._copy_kernel_headers,
            self._post_kernel_header_clean,
            self._switch_mounted_partition,
            self._copy_boot_files,
            self._unmount_device,
        ]
        for task in task_list:
            if task() is False:
                self.logger.info("Error encountered. Attempting to unmount /mnt...")
                self._unmount_device()
                return False

        return True

