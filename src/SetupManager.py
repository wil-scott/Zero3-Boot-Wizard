"""
SetupManager is responsible for ensuring that the user's workspace/environment is ready for the build process.
@author: Wil Scott
@date: April 2024
"""
import logging
import pathlib
import subprocess
import socket

class SetupManager:

    def __init__(self, block_device, defconfig=None):
        """
        Creates an instance of SetupManager.

        :param block_device: a string representing a micro-sd card to configure
        :param defconfig: the defconfig file used to compile the kernel
        :return: None
        """
        self.logger = logging.getLogger("config_tool")
        self.block_device = block_device
        self.defconfig = defconfig or "opz3_defconfig"

        # Status-related class variables
        self.internet_connection = False
        self.build_directory_status = False
        self.config_files_status = False
        self.block_device_status = False
        self.system_dependencies_status = False
        self.repositories_status = False
        self.device_mounts_status = False

        # class variables representing required files, directories, and repos necessary for kernel build/micro-sd card config
        self.config_files = {self.defconfig, "boot.scr", "expansion-board-overlay.dtbo"}
        self.packages = ["swig", "python3-dev", "build-essential", "device-tree-compiler", "git", "bison", "flex",
                         "python3-setuptools", "libssl-dev", "dosfstools", "libncurses-dev", "bc"]
        self.repositories = {
            "linux": "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git", 
            "u-boot": "git://git.denx.de/u-boot.git",
            "arm-trusted-firmware": "https://github.com/ARM-software/arm-trusted-firmware.git",
            "linux-firmware": "git://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git",
        }
        # Finished Init
        self.logger.info("SetupManager instantiated.")
        
    def _create_build_directory(self):
        """
        Creates build directory.

        :return: True if creation is successful, else False
        """
        try:
            pathlib.Path.mkdir("build")
            self.logger.info("Build directory created.")
            return True
        except FileExistsError:
            self.logger.info("Build directory already exists. Please rename or run tool with --clean flag")
            return False
        except Exception as e:
            self.logger.info("Error encountered while making build directory.")
            self.logger.error(e)
            return False

    def _check_internet_connection(self):
        """
        Connects to remote server (Google) in order to validate internet connection.

        :return: True if internet connection is verified, else False
        """
        remote_server = "www.google.com"
        port = 80
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((remote_server, port))
            self.logger.info("Connection to www.google.com successful. Internet connection verified.")
            return True
        except socket.error:
            self.logger.error("Unable to verify internet connection.")
            return False
        finally:
            sock.close()

    def _check_config_files_exist(self):
        """
        Confirms that "kernel_config" directory exists and contains only the necessary files.

        :return: True if only the expected files are present, else False 
        """
        # Confirm dir exists and get names of dir contents 
        if pathlib.Path("kernel_config").is_dir():
            temp_iterator = pathlib.Path("kernel_config").iterdir()
            config_directory_set = {obj_name.name for obj_name in temp_iterator}
        else:
            self.logger.error("Error accessing kernel_config directory.")
            return False

        # Convert lists to sets and confirm that mandatory configuration files are present
        if self.config_files.issubset(config_directory_set):
            self.logger.info("Mandatory configuration files present.")
            return True
        else:
            self.logger.info("Unable to validate configuration files - please verify contents of kernel_config directory.")
            return False

    def _check_block_device_exists(self):
        """
        Confirms that user's block device is connected to system.

        :return: True if block device detected, else False
        """
        # Get contents of sys/class/block
        temp_iterator = pathlib.Path("/sys/class/block").iterdir()
        block_devices = [devices.name for devices in temp_iterator]
        device_name = self.block_device.split('/')[-1]
        self.logger.debug(device_name)
        self.logger.debug(f"block devices: {block_devices}")
        # Confirm that user's block device present in list
        if device_name in block_devices:
            self.logger.info(f"User device {self.block_device} detected in system block devices.")
            return True
        else:
            self.logger.info(f"User device {self.block_device} not detected in system block devices. ")
            return False

    def _check_system_mounts(self):
        """
        Checks if user's block device is currently mounted in system. Also checks that /mnt directory is not
        currently in use.

        :return: True if block device not mounted and /mnt is available, else False
        """
        default_mount_point = "/mnt"
        
        with open("/proc/mounts", "r") as file:
            for line in file:
                fields = line.split()
                if len(fields) >= 2:
                    mounted_device, mount_point = fields[0], fields[1]
                    if mounted_device == self.block_device or mount_point == default_mount_point:
                        self.logger.error(f"{mounted_device} mounted on {mount_point}. /mnt must be free and block device must not be mounted.")
                        return False
        self.logger.info(f"{default_mount_point} is available and {self.block_device} not mounted.")
        return True

    def _check_system_dependencies(self):
        """
        Verifies that necessary packages have been installed. If not, calls function to install them.

        :return: True if packages installed or sucessfully installed, False if unable to install missing packages
        """
        for package in self.packages:
            try:
                subprocess.run(["dpkg", "-s", package], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.logger.info(f"Dependency found: {package}. Moving on...")
            except subprocess.CalledProcessError:
                self.logger.info(f"Unable to detect {package} in system. Attempting installation...")
                if self._install_system_dependency(package) is False:
                    return False
        return True

    def _install_system_dependency(self, package):
        """
        Install the package on the system.

        :param package: a String representing the missing package/dependency.
        :return: True if installation was sucessful, else False
        """
        try:
            subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully installed {package}.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.info(f"Failed to install {package}.")
            self.logger.error(e.stderr.decode())
            return False
 
    def _download_build_repositories(self, repository):
        """
        Clone repository into /repositories directory. 
        """
        destination = pathlib.Path(f"repositories/{repository}")
        try:
            if repository == "linux":
                subprocess.run(["git", "clone", self.repositories[repository], "--depth=1", str(destination)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.run(["git", "clone", self.repositories[repository], str(destination)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Successfully cloned {repository}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.info(f"Unable to clone {repository}.")
            self.logger.error(e.stderr.decode())
            return False
 
    def _check_repositories_exist(self):
        """
        Check that /repositories directory exists and contains necessary repos - create them if not.
        
        :return: True if directories present or created successfully, else False
        """
        repos_contents = list()

        if pathlib.Path("repositories").is_dir():
            # repository dir exists so we can check its contents
            self.logger.info("Repositories directory found. Checking contents...")
            temp_iterator = pathlib.Path("repositories").iterdir()
            repos_contents = [obj_name.name for obj_name in temp_iterator]
        
        else:
            try:
                pathlib.Path.mkdir("repositories")
                self.logger.info("Created respositories directory.")
            except Exception as e:
                self.logger.info("Unable to create repositories directory.")
                self.logger.error(e)
        
        # Confirm that 
        for item in self.repositories.keys():
            if item not in repos_contents:
                self.logger.info(f"Cloning {item}...")
                if self._download_build_repositories(item) is False:
                    return False
        return True

    def run_setup_manager(self):
        self.internet_connection = self._check_internet_connection()
        self.config_files_status = self._check_config_files_exist()
        self.block_device_status = self._check_block_device_exists()
        self.device_mounts_status = self._check_system_mounts()
        self.system_dependencies_status = self._check_system_dependencies()
        self.repositories_status = self._check_repositories_exist()
        self.build_directory_status = self._create_build_directory()
        self.logger.debug(self.internet_connection)
        self.logger.debug(self.build_directory_status)
        self.logger.debug(self.config_files_status)
        self.logger.debug(self.block_device_status)
        self.logger.debug(self.system_dependencies_status)
        self.logger.debug(self.repositories_status)
        self.logger.debug(self.device_mounts_status)
        
        if all([self.internet_connection, 
                self.build_directory_status, 
                self.config_files_status, 
                self.block_device_status, 
                self.system_dependencies_status,
                self.repositories_status,
                self.device_mounts_status]):
            return True
        else:
            return False

