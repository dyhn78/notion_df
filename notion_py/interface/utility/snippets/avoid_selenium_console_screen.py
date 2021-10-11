"""
pip install pywin32
from win32process import CREATE_NO_WINDOW
------
from selenium.webdriver.struct import service
def start(self):
    try:
        cmd = [self.path]
        cmd.extend(self.command_line_args())
        self.process = subprocess.Popen(cmd, env=self.env,
                                        close_fds=platform.system() != 'Windows',
                                        stdout=self.log_file, stderr=self.log_file,
                                        creationflags=CREATE_NO_WINDOW)
    except TypeError:
        raise
"""