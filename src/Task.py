"""
Task is responsible for running subprocess tasks on the user's system.
@Author: Wil Scott
@Date: April 2024
"""
import subprocess

class Task:
    def run_task(self, commands, cmd_input=None, cmd_text=None, cmd_cwd=None, use_shell=False, debug=False):
        """
        Run the commands via the subprocess module.

        :param commands: a list of strings OR a string representing the commands to be run
        :return: True if commands are successful, else False
        """
        try:
            subprocess.run(commands, check=True, input=cmd_input, text=cmd_text, shell=use_shell, cwd=cmd_cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"Command '{commands}' completed successfully.")
            if debug and not cmd_text:
                self.logger.debug(e.stdout.decode())
            return True
        except subprocess.SubprocessError as e:
            self.logger.info(f"Command '{commands}' failed.")
            if cmd_text:
                self.logger.error(e.stderr)
            else:
                self.logger.error(e.stderr.decode())
            return False

