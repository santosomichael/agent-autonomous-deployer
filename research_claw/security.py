import re
BLOCKED = [
 r'(^|\s)rm\s+-rf\s+/(\s|$)', r'(^|\s)mkfs\b', r'(^|\s)dd\s+.*\bof=/dev/',
 r'(^|\s)shutdown\b', r'(^|\s)reboot\b', r':\(\)\s*\{\s*:\|:&\s*;\s*\}:',
 r'(^|\s)passwd\b', r'(^|\s)userdel\b', r'(^|\s)iptables\s+-F\b'
]
def validate_command(command, allow_destructive=False):
    if not isinstance(command,str) or not command.strip(): raise ValueError("Empty command")
    if "\n" in command or "\r" in command: raise ValueError("Multiline commands are not allowed")
    if not allow_destructive:
        for pattern in BLOCKED:
            if re.search(pattern,command,re.I): raise ValueError(f"Blocked command pattern: {pattern}")
    return command
