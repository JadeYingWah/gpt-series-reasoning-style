"""
变异测试：修改rename.py的关键逻辑，验证测试能否发现
"""
import os
import shutil
import subprocess
import sys

SRC = r"<实验根目录>\ab-decoupled-code\A2plus\rename.py"
TEST_DIR = r"<实验根目录>\ab-decoupled-code\test_files"
MUTANT_DIR = r"<实验根目录>\ab-decoupled-code\A2plus\evidence\mutants"

def run_rename(script, directory, *args):
    """运行重命名工具，返回输出"""
    cmd = [sys.executable, script, directory] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr, result.returncode

def test_dry_run_no_modify(script):
    """测试1：dry-run不修改文件"""
    test_dir = os.path.join(MUTANT_DIR, "test_dryrun")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    shutil.copytree(TEST_DIR, test_dir)

    before = set(os.listdir(test_dir))
    run_rename(script, test_dir, "--prefix", "TEST_", "--dry-run")
    after = set(os.listdir(test_dir))

    shutil.rmtree(test_dir)
    return before == after, f"before={len(before)} after={len(after)}"

def test_numbered_correct(script):
    """测试2：序号填充正确（从start开始，width填充）"""
    test_dir = os.path.join(MUTANT_DIR, "test_numbered")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    shutil.copytree(TEST_DIR, test_dir)

    run_rename(script, test_dir, "--numbered", "--ext", ".png", "--start", "5", "--width", "2")
    files = sorted([f for f in os.listdir(test_dir) if f.endswith(".png")])

    shutil.rmtree(test_dir)
    # 应该是 image_1_05.png, image_2_06.png, ...
    expected = [f"image_{i}_{str(i+4).zfill(2)}.png" for i in range(1, 6)]
    return files == expected, f"got={files[:3]} expected={expected[:3]}"

def test_prefix_correct(script):
    """测试3：前缀添加正确（在文件名最前面）"""
    test_dir = os.path.join(MUTANT_DIR, "test_prefix")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    shutil.copytree(TEST_DIR, test_dir)

    run_rename(script, test_dir, "--prefix", "PRE_", "--ext", ".md")
    files = os.listdir(test_dir)

    shutil.rmtree(test_dir)
    return "PRE_readme.md" in files, f"files={files}"

def create_mutant(name, mutation_func):
    """创建变异版本"""
    os.makedirs(MUTANT_DIR, exist_ok=True)
    with open(SRC, encoding="utf-8") as f:
        code = f.read()
    mutated = mutation_func(code)
    path = os.path.join(MUTANT_DIR, f"rename_{name}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(mutated)
    return path

def mutation_remove_dryrun(code):
    """变异1：去掉dry-run检查（dry-run也实际修改）"""
    return code.replace("if not dry_run:\n                os.rename(filepath, new_path)", "os.rename(filepath, new_path)  # MUTANT: removed dry-run check")

def mutation_wrong_start(code):
    """变异2：序号起始值错误（start-1而不是start）"""
    return code.replace("idx = number_start if numbered else None", "idx = number_start - 1 if numbered else None  # MUTANT: wrong start")

def mutation_prefix_after_ext(code):
    """变异3：前缀加到扩展名后面"""
    return code.replace(
        'name = f"{prefix}{name}"',
        'name = f"{name}{prefix}"  # MUTANT: prefix after name (wrong position)'
    )

if __name__ == "__main__":
    os.makedirs(MUTANT_DIR, exist_ok=True)

    tests = [
        ("dry-run不修改文件", test_dry_run_no_modify),
        ("序号填充正确", test_numbered_correct),
        ("前缀位置正确", test_prefix_correct),
    ]

    mutants = [
        ("原始版本", None),
        ("去掉dry-run检查", mutation_remove_dryrun),
        ("序号起始值错误", mutation_wrong_start),
        ("前缀位置错误", mutation_prefix_after_ext),
    ]

    print("=" * 70)
    print("变异测试结果")
    print("=" * 70)

    for mutant_name, mutation_func in mutants:
        print(f"\n【{mutant_name}】")
        if mutation_func is None:
            script = SRC
        else:
            script = create_mutant(mutant_name, mutation_func)

        all_passed = True
        for test_name, test_func in tests:
            try:
                passed, detail = test_func(script)
                status = "PASS" if passed else "FAIL"
                if not passed:
                    all_passed = False
                print(f"  {status} - {test_name}: {detail}")
            except Exception as e:
                print(f"  ERROR - {test_name}: {e}")
                all_passed = False

        if mutation_func is not None:
            killed = not all_passed
            print(f"  >>> 变异体被{'杀死' if killed else '存活'}: {'测试发现了变异' if killed else '测试未发现变异'}")

    print("\n" + "=" * 70)
    print("结论：所有变异体应被测试杀死（即测试能发现代码错误）")
