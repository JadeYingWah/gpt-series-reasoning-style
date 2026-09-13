import sys
sys.path.insert(0, r"<实验根目录>\ab-metacognition\v1.2.3-test\v1.2.2")
from csv_parser import parse

# Extra tricky cases for bug sweep
cases = [
    ("single CR", "\r", [[]]),
    ("single CRLF", "\r\n", [[]]),
    ("a + CR no newline", "a\r", [["a"]]),
    ("quoted empty no newline", '""', [[""]]),
    ("lone quote", '"', "RAISE"),
    ("quote in middle no newline", 'a"b', [['a"b']]),
    ("content after close quote no newline", '"a"b', [["ab"]]),
    ("double BOM", "\ufeff\ufeffa", [["\ufeffa"]]),  # only first BOM skipped
    ("CRLF inside quotes", '"a\r\nb"\n', [["a\r\nb"]]),
    ("comma then EOF", "a,", [["a", ""]]),
    ("only comma", ",", [["", ""]]),
    ("only comma no newline", ",", [["", ""]]),
    ("space only field", " \n", [[" "]]),
    ("tab only field", "\t\n", [["\t"]]),
    ("unicode field", "姓名,年龄\n张三,30\n", [["姓名", "年龄"], ["张三", "30"]]),
    ("empty quoted between", 'a,"",b\n', [["a", "", "b"]]),
    ("multiple escaped quotes", '""""""\n', [['""']]),  # 6 quotes = 2 literal quotes
    ("quote comma quote", '"",""\n', [["", ""]]),
    ("NUL char", "a\x00b\n", [["a\x00b"]]),
    ("very long quoted with newline", '"' + "x"*1000 + "\n" + "y"*1000 + '"\n',
     [["x"*1000 + "\n" + "y"*1000]]),
]

passed = 0
failed = 0
for label, inp, expected in cases:
    try:
        result = parse(inp)
        if expected == "RAISE":
            print(f"FAIL: {label} — expected ValueError, got {result!r}")
            failed += 1
        elif result == expected:
            print(f"PASS: {label}")
            passed += 1
        else:
            print(f"FAIL: {label} — expected {expected!r}, got {result!r}")
            failed += 1
    except ValueError as e:
        if expected == "RAISE":
            print(f"PASS: {label} (raised ValueError)")
            passed += 1
        else:
            print(f"FAIL: {label} — unexpected ValueError: {e}")
            failed += 1
    except Exception as e:
        print(f"ERROR: {label} — {type(e).__name__}: {e}")
        failed += 1

print(f"\nBug sweep: {passed} passed, {failed} failed")
