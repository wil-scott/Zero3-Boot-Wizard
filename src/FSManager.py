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
        self.logger = logging.getLogger("config_tool")
        self.block_device = block_device
        self.root_partition = f"{block_device}2"
        self.mount_dir = "/mnt/"
        self.debian_release = "bookworm" 
        self.chroot_command_list = ["sudo", "chroot", self.mount_dir]

        self.logger.info("FSManager instantiated.")

    def _mount_device(self):
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

    def _unmount_device(self):
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

    def _bootstrap_stage_1(self):
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

    def _bootstrap_stage_2(self):
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
            self.logger.info(e.stdout.decode())
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _set_root_password(self):
        """
        Set root password in chroot environment for bootable image.

        :return: True if successful, else False
        """
        command_list = ["passwd"]
        password_input =  f"temp123\ntemp123\n"
        try:
            subprocess.run(self.chroot_command_list + command_list, input=password_input, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Password set to default value.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to set Root password in rootfs.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _update_hostname(self):
        """
        Set hostname for new bootable image.

        :return: True if successful, else False
        """
        command_list = ["echo", "orangepi", ">", "/etc/hostname"]
        command = " ".join(self.chroot_command_list + command_list)
        try:
            result = subprocess.run(command, check=True, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Hostname updated to default.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to update hostname in rootfs.")
            self.logger.error(e.stderr)
            return False

        return True

    def _enable_serial_console(self):
        """
        Enable serial console on rootfs for new bootable image.

        :return: True if successful else False
        """
        command_list = ["systemctl", "enable", "serial-getty@ttyS0.service"]
        try:
            subprocess.run(self.chroot_command_list + command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Serial console enabled on rootfs.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to enable serial console on rootfs.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _update_fstab(self):
        """
        Update file system table (fstab) to reflect system partitions/formatting.

        :return: True if successful, else False
        """
        fstab_content = (
            "none  /tmp	tmpfs	defaults,noatime,mode=1777	0	0\n"
            "/dev/mmcblk0p2	/	    ext4	defaults	0	1\n"
            "/dev/mmcblk0p1	/boot	vfat	defaults	0	2"
        )
        command_list = ["echo", f'"{fstab_content}"', ">", "/etc/fstab"]
        command = " ".join(self.chroot_command_list + command_list)
        self.logger.info(command)
        try:
            subprocess.run(command, check=True, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Successfully updated fstab in Rootfs.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to update /etc/fstab.")
            self.logger.error(e.stderr)
            return False

        return True

    def _update_apt_sources(self):
        """
        Update apt sources list to include standard Debian source list.

        :return: True if successful, else False
        """
        sources_list_content = (
            "deb http://deb.debian.org/debian bookworm main non-free-firmware\n"
            "deb-src http://deb.debian.org/debian bookworm main non-free-firmware\n"
            "deb http://deb.debian.org/debian-security/ bookworm-security main non-free-firmware\n"
            "deb-src http://deb.debian.org/debian-security/ bookworm-security main non-free-firmware\n"
            "deb http://deb.debian.org/debian bookworm-updates main non-free-firmware\n"
            "deb-src http://deb.debian.org/debian bookworm-updates main non-free-firmware"
        )
        command_list = ["echo", f'"{sources_list_content}"', ">", "/etc/apt/sources.list"]
        command = " ".join(self.chroot_command_list + command_list)
        try:
            subprocess.run(command, check=True, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Sources.list updated to standard debian source list.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to update sources.list.")
            self.logger.error(e.stderr)
            return False

        return True

    def _install_starter_packages(self):
        """
        Install networking and usb related packages into RootFS.

        :return: True if successful, else False
        """
        command_list = ["apt-get", "install", "-y", "network-manager", "wpasupplicant", "iw", "usbutils"]
        try:
            subprocess.run(self.chroot_command_list + command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Installed basic networking and usb packages successfully.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to install basic networking and usb packages.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def _cleanup(self):
        """
        Remove resolv.conf and run apt-get clean.

        :return: True if successful, else False
        """
        command_list_1 = ["apt-get", "clean"]
        command_list_2 = ["rm", "/etc/resolv.conf"]
        try:
            subprocess.run(self.chroot_command_list + command_list_1, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(self.chroot_command_list + command_list_2, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info("Clean up tasks complete.")
        except subprocess.SubprocessError as e:
            self.logger.info("Unable to complete clean up tasks.")
            self.logger.error(e.stderr.decode())
            return False

        return True

    def configure_rootfs(self):
        """
        Configure bootstrapped RootFS.

        :return: True if successful, else False
        """
        task_list = [
            self._mount_device,
            self._bootstrap_stage_1,
            self._bootstrap_stage_2,
            self._set_root_password,
            self._update_hostname,
            self._enable_serial_console,
            self._update_fstab,
            self._update_apt_sources,
            self._install_starter_packages,
            self._cleanup,
            self._unmount_device,
        ]

        for task in task_list:
            if task() is False:
                self.logger.info("Error encountered. Attempting to unmount /mnt...")
                self._unmount_device()
                return False

        return True

