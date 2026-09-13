"""变异测试 - 解耦版"""
import os, shutil, subprocess, sys

SRC = r"<实验根目录>\ab-decoupled-code\Decoupled\rename.py"
TEST_DIR = r"<实验根目录>\ab-decoupled-code\test_files"
MUTANT_DIR = r"<实验根目录>\ab-decoupled-code\Decoupled\evidence\mutants"

def run(script, d, *args):
    r = subprocess.run([sys.executable, script, d] + list(args), capture_output=True, text=True)
    return r.stdout + r.stderr

def test_dryrun(script):
    td = os.path.join(MUTANT_DIR, "t1"); os.makedirs(os.path.dirname(td), exist_ok=True)
    if os.path.exists(td): shutil.rmtree(td)
    shutil.copytree(TEST_DIR, td)
    b = set(os.listdir(td)); run(script, td, "--prefix", "T_", "--dry-run")
    a = set(os.listdir(td)); shutil.rmtree(td)
    return b == a

def test_numbered(script):
    td = os.path.join(MUTANT_DIR, "t2")
    if os.path.exists(td): shutil.rmtree(td)
    shutil.copytree(TEST_DIR, td)
    run(script, td, "--numbered", "--ext", ".png", "--start", "5", "--width", "2")
    files = sorted(f for f in os.listdir(td) if f.endswith(".png"))
    shutil.rmtree(td)
    return files == [f"image_{i}_{str(i+4).zfill(2)}.png" for i in range(1, 6)]

def test_prefix(script):
    td = os.path.join(MUTANT_DIR, "t3")
    if os.path.exists(td): shutil.rmtree(td)
    shutil.copytree(TEST_DIR, td)
    run(script, td, "--prefix", "P_", "--ext", ".md")
    ok = "P_readme.md" in os.listdir(td)
    shutil.rmtree(td)
    return ok

def mutant(name, func):
    os.makedirs(MUTANT_DIR, exist_ok=True)
    with open(SRC, encoding="utf-8") as f: code = f.read()
    p = os.path.join(MUTANT_DIR, f"m_{name}.py")
    with open(p, "w", encoding="utf-8") as f: f.write(func(code))
    return p

if __name__ == "__main__":
    tests = [("dry-run", test_dryrun), ("序号", test_numbered), ("前缀", test_prefix)]
    mutants = [
        ("原始", None),
        ("去掉dry-run", lambda c: c.replace("if not dry:\n                os.rename(f, nf)", "os.rename(f, nf)  # M")),
        ("序号起始错", lambda c: c.replace("idx = start if numbered else None", "idx = start - 1 if numbered else None  # M")),
        ("前缀位置错", lambda c: c.replace('name = f"{prefix}{name}"', 'name = f"{name}{prefix}"  # M')),
    ]
    for mname, mfunc in mutants:
        print(f"\n【{mname}】")
        script = SRC if mfunc is None else mutant(mname, mfunc)
        allok = True
        for tname, tfunc in tests:
            ok = tfunc(script)
            allok = allok and ok
            print(f"  {'PASS' if ok else 'FAIL'} - {tname}")
        if mfunc:
            print(f"  >>> {'被杀死' if not allok else '存活'}")
