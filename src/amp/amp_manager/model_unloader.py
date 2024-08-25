import threading
from typing import Callable


class ModelUnloader:
    def __init__(self, func: Callable[[], None], unload_timeout: int = 600):
        self.func = func
        self.unload_timeout = unload_timeout
        self.unload_timer = None

    def set_unload_timer(self):
        self.unload_timer = threading.Timer(self.unload_timeout, self.func)
        self.unload_timer.start()

    def cancel_unload_timer(self):
        if self.unload_timer:
            self.unload_timer.cancel()
