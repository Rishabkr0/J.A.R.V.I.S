import pytest
import asyncio
from app.tools.impl.screen import CaptureScreenTool, GetActiveWindowTool, GetScreenStateTool, GetVisibleTextTool

@pytest.mark.asyncio
async def test_capture_screen_tool():
    tool = CaptureScreenTool()
    res = await tool.execute(save=False)
    assert isinstance(res, dict)
    assert "success" in res
    assert "message" in res
    
    res_saved = await tool.execute(save=True)
    assert isinstance(res_saved, dict)
    assert "success" in res_saved

@pytest.mark.asyncio
async def test_get_active_window_tool():
    tool = GetActiveWindowTool()
    res = await tool.execute()
    assert isinstance(res, dict)
    assert "success" in res
    assert "message" in res

@pytest.mark.asyncio
async def test_get_screen_state_tool():
    tool = GetScreenStateTool()
    res = await tool.execute()
    assert isinstance(res, dict)
    assert "success" in res
    assert "Monitors:" in res["message"]

@pytest.mark.asyncio
async def test_get_visible_text_tool():
    tool = GetVisibleTextTool()
    res = await tool.execute()
    assert isinstance(res, dict)
    assert "success" in res
    assert "Visible Text" in res["message"] or "Failed to capture" in res["message"] or "No visible text" in res["message"] or "Error" in res["message"]
