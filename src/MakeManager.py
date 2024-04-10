"""
MakeManager is responsible for running the buid commands necessary to compile the components of the bootable image. 
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess
import socket

class MakeManager:

    def __init__(self, block_device, defconfig=None):
        """
        Initializes an object of class MakeManager.

        :param block_device: a String representing the name of the block device meant to store the bootable image
        :param defconfig: a String, representing the name of the defconfig to be used for kernel compilation
        """
        self.logger = logging.getLogger("config_tool")
        self.block_device = block_device
        self.defconfig = defconfig or "opz3_defconfig"

        # Make command variables
        self.nproc = self._get_nproc()
        self.arch = "ARCH=arm64"
        self.cross_comp = "CROSS_COMPILE=aarch64-linux-gnu-"

        # File paths for bootable image files
        self.bl31_path = "repositories/arm-trusted-firmware/build/sun50i_h616/debug/bl31.bin"
        self.uboot_spl_path = "repositories/u-boot/u-boot-sunxi-with-spl.bin"
        self.image_path = "repositories/linux/arch/arm64/boot/Image"
        self.dtb_path = "repositories/linux/arch/arm64/boot/dts/allwinner/sun50i-h618-orangepi-zero3.dtb"

        self.logger.info("MakeManager Instantiated.")

    def _get_nproc(self):
        """
        Determine number of cores present on system to speed up compilation process.

        :return: a string representing the numerical value of the number of cores on the user's system
        """
        command_list = ["nproc"]
        try:
            result = subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"nproc command successful. Setting nproc to {result.stdout.decode().strip()}.")
            return int(result.stdout.decode().strip())
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to query system for core/proc amount. Setting nproc to 1 as default.")
            self.logger.error(e.stderr.decode())
            return 1 

    def _check_for_file(self, file_name, file_directory):
        """
        Check if a file has already been made.
        
        :param file_name: a String representing the name of the file to search for
        :param file_directory: a String representing the directory path in which the file could be in
        :return: True if file is present in given directory, else False
        """
         # Confirm dir exists and get names of dir contents 
        if pathlib.Path(file_directory).is_dir():
            temp_iterator = pathlib.Path(file_directory).iterdir()
            directory_contents = [obj_name.name for obj_name in temp_iterator]
        else:
            self.logger.info(f"{file_name} not found in {file_directory}.")
            return False

        # search for file
        if file_name in directory_contents:
            self.logger.info(f"{file_name} found in {file_directory}. Moving on...")
            return True
        else:
            self.logger.info(f"{file_name} not found in {file_directory}. Making {file_name}...")
            return False

    def _make_bl31(self):
        """
        Make bl31.bin with Arm trusted firmware repo.

        :return: True if successful, else False
        """
        command_list = ["make", self.cross_comp, "PLAT=sun50i_h616", "DEBUG=1", "bl31"]
        repo_dir = "repositories/arm-trusted-firmware/"

        # Check if bl31 already exists
        if pathlib.Path(self.bl31_path).exists():
            self.logger.info("bl31.bin found in tf-a repo. Moving on...")
            return True

        try:
            subprocess.run(command_list, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Successfully compiled bl31 in arm-trusted-firmware.")
        except subproces.SubprocessError as e:
            self.logger.info("Unable to compile tf-a bl31.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _make_uboot(self):
        """
        Make .spl file with bl31 and u-boot.

        :return: True if successful, else False
        """
        command_list_1 = ["make", self.cross_comp, "BL31=../arm-trusted-firmware/build/sun50i_h616/debug/bl31.bin", "orangepi_zero3_defconfig"]
        command_list_2 = ["make", self.cross_comp, "BL31=../arm-trusted-firmware/build/sun50i_h616/debug/bl31.bin"]
        repo_dir = "repositories/u-boot"
        
        # Check if u-boot .bin file already exists
        if pathlib.Path(self.uboot_spl_path).exists():
            self.logger.info("u-boot-sunxi-with-spl.bin found in u-boot repo. Moving on...")
            return True

        try:
            subprocess.run(command_list_1, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Set u-boot recipe to orange pi zero3 defconfig.")
            subprocess.run(command_list_2, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Made u-boot .bin successfully.")
        except subprocess.SubprocessError as e:
            self.logger.info("Failed to make uboot .bin file.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _make_image(self):
        """
        Make linux kernel image.

        :return: True if successful, else False
        """
        command_list_1 = ["sudo", self.arch, self.cross_comp, "make", self.defconfig]
        command_list_2 = ["sudo", self.arch, self.cross_comp, "make", "Image", f"-j{self.nproc}"]
        repo_dir = "repositories/linux"
        
        # Check if Image already exists
        if pathlib.Path(self.image_path).exists():
            self.logger.info("Image found in linux repo. Moving on...")
            return True

        try:
            subprocess.run(command_list_1, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Set kernel image recipe to {self.defconfig}.")
            subprocess.run(command_list_2, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Made kernel image successfully.")
        except subprocess.SubprocessError as e:
            self.logger.info("Failed to make kernel image.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _make_device_tree(self):
        """
        Make Device Tree Binary.

        :return: True if successful, else False
        """
        command_list = ["sudo", self.arch, self.cross_comp, "make", "dtbs", f"-j{self.nproc}" ]
        repo_dir = "repositories/linux"

        # Check if dtb already exists
        if pathlib.Path(self.dtb_path).exists():
            self.logger.info(".dtb file found in linux repo. Moving on...")
            return True

        try:
            subprocess.run(command_list, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Made device tree binary sucessfully.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to compile device tree binary.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _make_modules(self):
        """
        Make image modules.

        :return: True if successful, else False
        """
        command_list = ["sudo", self.arch, self.cross_comp, "make", "modules", f"-j{self.nproc}"]
        repo_dir = "repositories/linux"
        try:
            subprocess.run(command_list, cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Made modules successfully.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to compile kernel modules.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def run_uboot_make_commands(self):
        """
        Run bootloader-related make commands.

        :return: True if successful, else False
        """
        task_list = [
            self._make_bl31,
            self._make_uboot,
        ]

        for task in task_list:
            if task() is False:
                return False

        return True

    def run_linux_make_commands(self):
        """
        Run linux-related make commands.

        :return: True if successful, else False
        """
        task_list = [
            self._make_image,
            self._make_device_tree,
            self._make_modules
        ]

        for task in task_list:
            if task() is False:
                return False

        return True

