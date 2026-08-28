import ctypes
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("jarvis.tools.gui_context")

class GUITargetContext:
    _instance = None

    def __init__(self):
        self.handle: Optional[int] = None
        self.title: Optional[str] = None
        self.process_name: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "GUITargetContext":
        if cls._instance is None:
            cls._instance = GUITargetContext()
        return cls._instance

    def set_target(self, handle: Optional[int], title: Optional[str], process_name: Optional[str] = None):
        self.handle = handle
        self.title = title
        self.process_name = process_name
        logger.info(f"GUI Target Context UPDATED: handle={handle}, title='{title}', process='{process_name}'")

    def clear(self):
        if self.handle:
            logger.info(f"GUI Target Context CLEARED (was handle={self.handle}, title='{self.title}')")
        self.handle = None
        self.title = None
        self.process_name = None

    def is_valid(self) -> bool:
        if not self.handle:
            return False
        try:
            user32 = ctypes.windll.user32
            if not user32.IsWindow(self.handle):
                logger.info(f"Target window handle {self.handle} is no longer valid.")
                self.clear()
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking window handle validity: {e}")
            self.clear()
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": self.handle,
            "title": self.title,
            "process_name": self.process_name,
            "is_valid": self.is_valid()
        }
