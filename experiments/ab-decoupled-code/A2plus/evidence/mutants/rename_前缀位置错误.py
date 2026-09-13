#!/usr/bin/env python3
"""
批量重命名命令行工具（A2+配置版）
支持：前缀添加、序号填充、正则替换、dry-run、递归、扩展名过滤
"""
import argparse
import os
import re
import sys
from pathlib import Path


def collect_files(directory, recursive=False, ext_filter=None):
    """收集目标文件列表"""
    files = []
    if recursive:
        for root, _, filenames in os.walk(directory):
            for f in filenames:
                if ext_filter and not f.endswith(ext_filter):
                    continue
                files.append(os.path.join(root, f))
    else:
        for f in os.listdir(directory):
            full = os.path.join(directory, f)
            if os.path.isfile(full):
                if ext_filter and not f.endswith(ext_filter):
                    continue
                files.append(full)
    return sorted(files)


def apply_transforms(filepath, prefix=None, regex_pat=None, regex_repl=None,
                     index=None, number_width=3):
    """对单个文件名应用变换，返回新文件名"""
    directory = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    name, ext = os.path.splitext(basename)

    # 正则替换（先执行，作用于name部分）
    if regex_pat:
        name = re.sub(regex_pat, regex_repl or "", name)

    # 序号填充
    if index is not None:
        name = f"{name}_{str(index).zfill(number_width)}"

    # 前缀添加（最后执行）
    if prefix:
        name = f"{name}{prefix}"  # MUTANT: prefix after name (wrong position)

    return os.path.join(directory, name + ext)


def execute_rename(files, prefix=None, regex_pat=None, regex_repl=None,
                   numbered=False, number_start=1, number_width=3,
                   dry_run=False):
    """执行重命名，返回(操作列表, 错误列表)"""
    operations = []
    errors = []
    idx = number_start if numbered else None

    for filepath in files:
        try:
            new_path = apply_transforms(
                filepath, prefix=prefix,
                regex_pat=regex_pat, regex_repl=regex_repl,
                index=idx, number_width=number_width
            )

            if new_path == filepath:
                operations.append((filepath, filepath, "skipped (no change)"))
                continue

            # 检查目标是否已存在
            if os.path.exists(new_path):
                errors.append((filepath, new_path, "target already exists"))
                continue

            if not dry_run:
                os.rename(filepath, new_path)

            operations.append((filepath, new_path, "renamed" if not dry_run else "dry-run"))
        except Exception as e:
            errors.append((filepath, None, str(e)))

        if numbered:
            idx += 1

    return operations, errors


def main():
    parser = argparse.ArgumentParser(description="批量重命名工具")
    parser.add_argument("directory", help="目标目录")
    parser.add_argument("--prefix", help="添加前缀")
    parser.add_argument("--regex", help="正则匹配模式（作用于文件名不含扩展名）")
    parser.add_argument("--replacement", help="正则替换内容", default="")
    parser.add_argument("--numbered", action="store_true", help="添加序号")
    parser.add_argument("--start", type=int, default=1, help="序号起始值")
    parser.add_argument("--width", type=int, default=3, help="序号填充宽度")
    parser.add_argument("--recursive", action="store_true", help="递归子目录")
    parser.add_argument("--ext", help="按扩展名过滤（如 .txt）")
    parser.add_argument("--dry-run", action="store_true", help="只预览不执行")

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"错误：目录不存在 - {args.directory}", file=sys.stderr)
        sys.exit(1)

    if not any([args.prefix, args.regex, args.numbered]):
        print("错误：至少指定一种变换（--prefix/--regex/--numbered）", file=sys.stderr)
        sys.exit(1)

    files = collect_files(args.directory, recursive=args.recursive, ext_filter=args.ext)

    if not files:
        print("未找到匹配文件")
        return

    operations, errors = execute_rename(
        files,
        prefix=args.prefix,
        regex_pat=args.regex,
        regex_repl=args.replacement,
        numbered=args.numbered,
        number_start=args.start,
        number_width=args.width,
        dry_run=args.dry_run,
    )

    print(f"{'模式':<10} {'原文件':<40} {'新文件'}")
    print("-" * 90)
    for old, new, status in operations:
        print(f"{status:<10} {os.path.basename(old):<40} {os.path.basename(new)}")

    if errors:
        print(f"\n错误 ({len(errors)}):")
        for old, new, err in errors:
            print(f"  {os.path.basename(old)}: {err}")

    print(f"\n总计：{len(operations)} 操作，{len(errors)} 错误")
    if args.dry_run:
        print("（dry-run 模式，未实际修改文件）")


if __name__ == "__main__":
    main()
