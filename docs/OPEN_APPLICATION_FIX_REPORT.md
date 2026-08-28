# OPEN_APPLICATION Robustness Fix Report

## Root Cause
The hanging behavior was caused by the combination of an unreliable Windows launch mechanism (`os.startfile`) and the previously fixed frontend state management bug. While `os.startfile()` does not technically block the Python thread, it operates asynchronously through the Windows Shell (`ShellExecute`). When run from a background daemon, a non-interactive shell, or when relying on incomplete environment paths, `os.startfile` can fail to surface the application correctly, swallow errors, or spawn the application in an inaccessible session context without raising a Python exception. 

Because it swallowed the failure or hung in the shell broker, the backend blindly returned success, but the frontend could not progress if the shell was stalled or the window wasn't actually pushed to the foreground interactive session.

## Exact File/Function Responsible
- **File:** `backend/app/tools/impl/windows_apps.py`
- **Function:** `OpenAppTool.execute()`
- **Mechanism:** `os.startfile(exe)` relying blindly on the shell.

## Fix Applied
1. **Robust Path Resolver (`_find_executable`)**: Replaced raw executable names with a deterministic resolver that explicitly searches:
   - The environment `PATH` (using `shutil.which`)
   - The system Registry (`HKEY_LOCAL_MACHINE` App Paths)
   - The user Registry (`HKEY_CURRENT_USER` App Paths)
2. **Explicit Detached Launch (`subprocess.Popen`)**: Replaced `os.startfile()` with `subprocess.Popen(..., creationflags=0x00000008, close_fds=True)`. This explicitly creates a detached process (`DETACHED_PROCESS = 0x00000008`) directly pointing to the resolved executable, guaranteeing it surfaces in the current session without blocking or depending on shell quirks.
3. **Graceful Failures**: If the executable cannot be resolved, the tool now generates an explicit `EXECUTABLE_NOT_FOUND` error, which triggers `TOOL_ERROR` in the backend and correctly returns the UI to `IDLE`.

## Tests Performed
- **Clean State**: Used `psutil` to explicitly kill all Chrome and Notepad processes before testing.
- **Chrome Launch**: Issued "Open Chrome". 
  - Verified path resolution via Registry (`C:\Program Files\Google\Chrome\Application\chrome.exe`).
  - Verified `Popen` dispatch.
  - Verified `psutil` successfully detected the newly launched `chrome.exe` process.
- **Notepad Launch**: Issued "Open Notepad".
  - Verified path resolution via PATH (`C:\WINDOWS\system32\notepad.exe`).
  - Verified `Popen` dispatch and process creation.
- **Invalid App Handling**: Issued "Open FakeApp" (bypassing FastRouter restriction for testing).
  - Verified the resolver correctly failed to find it.
  - Verified the tool returned `success: False`.
  - Verified the Orchestrator safely emitted `TOOL_ERROR` and returned to `IDLE` instead of hanging.
- **Gemini Bypass**: Verified `FastRouter` executed all these operations locally in `<0.07s` without contacting the Gemini API.
- **Test Suites**: PyTest passed 18/18 tests, and TypeScript compiled with 0 errors.

## Final Validation
Chrome and Notepad successfully launch. Gemini was completely bypassed. The UI returns gracefully to IDLE upon both success and failure.
