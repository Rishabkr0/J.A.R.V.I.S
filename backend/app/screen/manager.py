import logging
import io
import mss
import tempfile
import os
import ctypes
import psutil
import asyncio
from PIL import Image

try:
    from pywinauto import Desktop
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

logger = logging.getLogger("jarvis.screen.manager")

class ScreenManager:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def get_monitor_info(self):
        try:
            with mss.MSS() as sct:
                monitors = []
                for i, m in enumerate(sct.monitors):
                    if i == 0: continue # Monitor 0 is a virtual monitor comprising all
                    monitors.append({
                        "id": i,
                        "width": m["width"],
                        "height": m["height"],
                        "left": m["left"],
                        "top": m["top"],
                        "is_primary": m.get("is_primary", False)
                    })
                return {"monitors": monitors, "count": len(monitors)}
        except Exception as e:
            logger.error(f"Error getting monitor info: {e}")
            return {"error": str(e)}

    def capture_screenshot(self, monitor_id: int = 1, save_to_disk: bool = False):
        """Captures screenshot to an in-memory buffer, optionally saving to disk if requested."""
        try:
            with mss.MSS() as sct:
                if monitor_id >= len(sct.monitors):
                    monitor_id = 1 # Fallback to primary
                monitor = sct.monitors[monitor_id]
                screenshot = sct.grab(monitor)
                
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='BMP')
                
                result = {
                    "bytes": img_bytes.getvalue(),
                    "size": screenshot.size
                }
                
                if save_to_disk:
                    save_path = os.path.join(self.temp_dir, "jarvis_screenshot.png")
                    img.save(save_path, format="PNG")
                    result["saved_path"] = save_path
                    
                return result
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return {"error": f"Screen capture failed: {e}"}

    def get_active_window_fast(self):
        """Instant Win32 API fetch of active window details without UIA tree scanning."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return {"error": "No active window found or desktop locked."}
                
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or "Unknown"
            
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            process_name = "Unknown"
            try:
                proc = psutil.Process(pid.value)
                process_name = proc.name()
            except:
                pass
                
            rect = [0, 0, 0, 0]
            try:
                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                r = RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                rect = [r.left, r.top, r.right - r.left, r.bottom - r.top]
            except:
                pass
                
            return {
                "title": title,
                "process": process_name,
                "pid": pid.value,
                "rect": rect
            }
        except Exception as e:
            logger.error(f"Error getting fast active window: {e}")
            return {"error": str(e)}

    def get_active_window_uia(self):
        """Scans active window UIA control hierarchy with safe fallback."""
        if not PYWINAUTO_AVAILABLE:
            return self.get_active_window_fast()
            
        try:
            desktop = Desktop(backend="uia")
            active = desktop.window(active_only=True)
            if not active.exists():
                return self.get_active_window_fast()
                
            rect = active.rectangle()
            state = {
                "title": active.window_text() or "Unknown",
                "process": active.process_id(),
                "rect": [rect.left, rect.top, rect.width(), rect.height()],
                "controls": []
            }
            
            # Enumerate controls with safety timeout/limit
            for d in active.descendants():
                try:
                    elem_text = d.window_text()
                    elem_type = d.friendly_class_name()
                    crect = d.rectangle()
                    if elem_text and elem_text.strip():
                        state["controls"].append({
                            "type": elem_type,
                            "text": elem_text.strip()[:100],
                            "rect": [crect.left, crect.top, crect.width(), crect.height()]
                        })
                        if len(state["controls"]) >= 40:
                            break
                except:
                    pass
            return state
        except Exception as e:
            logger.warning(f"UIA scan failed/timed out: {e}. Falling back to fast Win32 API.")
            return self.get_active_window_fast()

    async def get_ocr_text(self, img_bytes: bytes):
        """Native Windows Runtime OCR engine lazy import."""
        try:
            import winrt.windows.media.ocr as ocr
            import winrt.windows.graphics.imaging as imaging
            import winrt.windows.storage.streams as streams
            import winrt.windows.globalization as globalization
            WINRT_AVAILABLE = True
        except ImportError:
            WINRT_AVAILABLE = False
            
        if not WINRT_AVAILABLE:
            return {"error": "winrt OCR not available"}
            
        try:
            data_writer = streams.DataWriter()
            data_writer.write_bytes(img_bytes)
            ibuffer = data_writer.detach_buffer()
            
            stream = streams.InMemoryRandomAccessStream()
            await stream.write_async(ibuffer)
            stream.seek(0)
            
            decoder = await imaging.BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()
            
            lang = globalization.Language("en-US")
            if not ocr.OcrEngine.is_language_supported(lang):
                return {"error": "en-US language not supported by native OCR"}
                
            engine = ocr.OcrEngine.try_create_from_language(lang)
            result = await engine.recognize_async(software_bitmap)
            
            lines = []
            for line in result.lines:
                lines.append(line.text)
                if len(lines) >= 50:
                    break
                
            return {"lines": lines, "text": result.text, "count": len(lines)}
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return {"error": str(e)}
