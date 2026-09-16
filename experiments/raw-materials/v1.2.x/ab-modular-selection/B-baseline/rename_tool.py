#!/usr/bin/env python3
"""文件批量重命名工具"""
import os
import re
import argparse
from pathlib import Path

def rename_files(directory, prefix="", suffix="", start_num=1, padding=3, pattern=None, replace=None, dry_run=False):
    path = Path(directory)
    if not path.is_dir():
        print(f"错误: {directory} 不是有效目录")
        return

    files = sorted([f for f in path.iterdir() if f.is_file()])
    count = 0

    for i, f in enumerate(files):
        name = f.stem
        ext = f.suffix

        # 正则替换
        if pattern and replace:
            name = re.sub(pattern, replace, name)

        # 序号
        num = str(start_num + i).zfill(padding)

        # 新文件名
        new_name = f"{prefix}{name}{num}{suffix}{ext}"
        new_path = path / new_name

        if dry_run:
            print(f"[预览] {f.name} -> {new_name}")
        else:
            f.rename(new_path)
            print(f"{f.name} -> {new_name}")
        count += 1

    print(f"\n共处理 {count} 个文件")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="文件批量重命名工具")
    parser.add_argument("directory", help="目标目录")
    parser.add_argument("--prefix", default="", help="文件名前缀")
    parser.add_argument("--suffix", default="", help="文件名后缀")
    parser.add_argument("--start", type=int, default=1, help="起始序号")
    parser.add_argument("--padding", type=int, default=3, help="序号位数")
    parser.add_argument("--pattern", help="正则匹配模式")
    parser.add_argument("--replace", help="替换文本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    args = parser.parse_args()

    rename_files(args.directory, args.prefix, args.suffix, args.start, args.padding, args.pattern, args.replace, args.dry_run)
