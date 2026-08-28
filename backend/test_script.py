import asyncio
import logging
import psutil
from app.orchestrator.core import Orchestrator

logging.basicConfig(level=logging.INFO)

def kill_app(app_name):
    count = 0
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and app_name in proc.info['name'].lower():
            try:
                proc.kill()
                count += 1
            except:
                pass
    return count

def check_app(app_name):
    return any(app_name in proc.info['name'].lower() for proc in psutil.process_iter(['name']) if proc.info['name'])

async def test_integration():
    print(f'Killed {kill_app("chrome")} chrome processes.')
    print(f'Killed {kill_app("notepad")} notepad processes.')
    await asyncio.sleep(1)
    
    orch = Orchestrator()
    print('\n=== Testing: Open Chrome ===')
    await orch.handle_chat_message('test-session', 'Open Chrome')
    await asyncio.sleep(2)
    print(f'Chrome successfully launched: {check_app("chrome")}')
    
    print('\n=== Testing: Open Notepad ===')
    await orch.handle_chat_message('test-session', 'Open Notepad')
    await asyncio.sleep(2)
    print(f'Notepad successfully launched: {check_app("notepad")}')

    print('\n=== Testing: Open FakeApp ===')
    from app.tools.registry import ToolRegistry
    tool = ToolRegistry.get_tool('open_application')
    tool.KNOWN_APPS['fakeapp'] = 'fakeapp_does_not_exist.exe'
    
    # We must patch FastRouter to allow FakeApp to bypass Gemini
    from app.orchestrator.fast_router import FastRouter
    orch.fast_router.rules[0] = (r'^(?:open|launch|start) (chrome|edge|notepad|calculator|terminal|explorer|cmd|fakeapp)$', orch.fast_router.rules[0][1])
    
    await orch.handle_chat_message('test-session', 'Open FakeApp')

asyncio.run(test_integration())
