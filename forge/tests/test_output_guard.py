"""Tests for forge.py detect_tool_invocation — mirrors Go-side output_guard_test.go"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forge import detect_tool_invocation


def test_clean_code():
    assert detect_tool_invocation("package main\n\nfunc main() {}\n") is False

def test_awaiting_permission():
    assert detect_tool_invocation("Awaiting permission to write the file...") is True

def test_please_approve():
    assert detect_tool_invocation("Please approve the file write operation.") is True

def test_ready_to_create():
    assert detect_tool_invocation("I'm ready to create the useToast hook. Please allow me to write the file.") is True

def test_write_file_in_instructions_ok():
    # This is an instruction, not a permission request — contains "import"
    assert detect_tool_invocation("NAO use write_file. import os. Retorne APENAS codigo.") is False

def test_normal_text():
    assert detect_tool_invocation("Write the handler function that validates input.") is False

def test_empty():
    assert detect_tool_invocation("") is False

def test_short_junk():
    assert detect_tool_invocation("OK") is False

def test_mixed_code_plus_permission():
    # Has real code indicator — should be considered usable
    assert detect_tool_invocation("package main\n\nfunc main() {}\n\nAwaiting permission") is False

def test_python_code():
    assert detect_tool_invocation("def hello():\n    return 'world'\n") is False

def test_let_me_write():
    assert detect_tool_invocation("Let me write the file for you.") is True


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
