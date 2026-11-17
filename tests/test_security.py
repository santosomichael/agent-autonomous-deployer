from research_claw.security import validate_command

def test_safe(): assert validate_command('nvidia-smi') == 'nvidia-smi'
def test_blocked():
    try: validate_command('rm -rf /')
    except ValueError: return
    raise AssertionError('dangerous command was not blocked')
