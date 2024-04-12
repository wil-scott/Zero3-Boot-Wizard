"""
FSmanager is responsible for bootstrapping the Debian RootFS onto the Micro-SD Card.
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess

from src.Task import Task

class FSManager(Task):

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
        return self.run_task(command_list)

    def _unmount_device(self):
        """
        Unmount the root partition from /mnt.

        :return: True if unmount command successful, else False
        """
        command_list = ["sudo", "umount", "/mnt"]
        return self.run_task(command_list)

    def _bootstrap_stage_1(self):
        """
        Run stage 1 of debootstrap.

        :return: True if successful, else False
        """
        command_list = ["sudo", "debootstrap", "--arch=arm64", "--foreign", self.debian_release, self.mount_dir]
        return self.run_task(command_list)

    def _bootstrap_stage_2(self):
        """
        Run second stage of Debootstrap in chrooted /mnt.

        :return: True if successful, else False
        """
        command_list = ["/debootstrap/debootstrap", "--second-stage"]
        return self.run_task(self.chroot_command_list + command_list)

    def _set_root_password(self):
        """
        Set root password in chroot environment for bootable image.

        :return: True if successful, else False
        """
        command_string = f'sudo chroot {self.mount_dir} chpasswd'
        password_input = "root:temp"
        return self.run_task(command_string, use_shell=True, cmd_text=True, cmd_input=password_input)

    def _update_hostname(self):
        """
        Set hostname for new bootable image.

        :return: True if successful, else False
        """
        command_list = ["echo", "orangepi", ">", "/etc/hostname"]
        command = " ".join(self.chroot_command_list + command_list)
        return self.run_task(command, cmd_text=True, use_shell=True)

    def _enable_serial_console(self):
        """
        Enable serial console on rootfs for new bootable image.

        :return: True if successful else False
        """
        command_list = ["systemctl", "enable", "serial-getty@ttyS0.service"]
        return self.run_task(self.chroot_command_list + command_list)

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
        #command = f"echo '{fstab_content}' > /etc/fstab"
        #command = " ".join(self.chroot_command_list + command_list)
        #return self.run_task(command, cmd_text=True, use_shell=True)
        try:
            with subprocess.Popen(self.chroot_command_list + ["tee", "/etc/fstab"], stdin=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                proc.communicate(input=fstab_content.encode())
                if proc.returncode != 0:
                    raise subprocess.SubprocessError(proc.stderr)
            self.logger.info("Updated fs table.")
            return True
        except subprocess.SubprocessError as e:
            self.logger.info("Failed to update fs table.")
            self.logger.error(e.decode())
            return False


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
        try:
            with subprocess.Popen(self.chroot_command_list + ["tee", "/etc/apt/sources.list"], stdin=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                proc.communicate(input=sources_list_content.encode())
                if proc.returncode != 0:
                    raise subprocess.SubprocessError(proc.stderr)
            self.logger.info("Updated sources.list.")
            return True
        except subprocess.SubprocessError as e:
            self.logger.info("Failed to update sources.list.")
            self.logger.error(e.decode())
            return False
        #command = f"echo '{sources_list_content}' > /etc/apt/sources.list"
        #command = " ".join(self.chroot_command_list + command_list)
        #return self.run_task(command, cmd_text=True, use_shell=True)

    def _install_starter_packages(self):
        """
        Install networking and usb related packages into RootFS.

        :return: True if successful, else False
        """
        command_list = ["apt-get", "install", "-y", "network-manager", "wpasupplicant", "iw", "usbutils"]
        return self.run_task(self.chroot_command_list + command_list)

    def _cleanup(self):
        """
        Remove resolv.conf and run apt-get clean.

        :return: True if successful, else False
        """
        commands = {
            1: ["apt-get", "clean"],
            2: ["rm", "/etc/resolv.conf"],
        }
        
        for key in commands.keys():
            if self.run_task(self.chroot_command_list + commands[key]) is False:
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

