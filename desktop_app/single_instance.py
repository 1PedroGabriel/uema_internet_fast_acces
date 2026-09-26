import sys
import ctypes

ERROR_ALREADY_EXISTS = 183

class SingleInstance:
    """
    Garante que apenas uma única instância do processo rode por vez no Windows,
    usando um Named Mutex no nível do Kernel.
    """
    def __init__(self, mutex_name="Global\\UEMA_Internet_FastAccess_Mutex"):
        self.mutex_name = mutex_name
        self.mutex = None

    def is_already_running(self):
        if sys.platform != "win32":
            return False
        
        self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        return last_error == ERROR_ALREADY_EXISTS

    def release(self):
        if self.mutex and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None
