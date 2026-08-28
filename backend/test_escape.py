def escape_pywinauto_keys(text: str) -> str:
    chars = []
    for c in text:
        if c in ("{", "}", "^", "%", "+", "~"):
            chars.append(f"{{{c}}}")
        else:
            chars.append(c)
    return "".join(chars)

print("Escaped:", escape_pywinauto_keys("Hello + World! {Test} ^100%"))
