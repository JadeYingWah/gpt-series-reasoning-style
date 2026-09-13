#!/usr/bin/env python3
"""
文件批量重命名工具
支持：前缀/后缀/序号/正则替换/预览模式
"""
import os
import re
import argparse
from pathlib import Path


def rename_files(directory, prefix="", suffix="", start_num=1, padding=3,
                 pattern=None, replace=None, dry_run=False):
    """批量重命名目录中的文件"""
    path = Path(directory)
    if not path.is_dir():
        print(f"错误: '{directory}' 不是有效目录")
        return 1

    files = sorted([f for f in path.iterdir() if f.is_file()])
    if not files:
        print(f"目录 '{directory}' 中没有文件")
        return 0

    count = 0
    errors = 0

    for i, f in enumerate(files):
        try:
            name = f.stem
            ext = f.suffix

            # 正则替换
            if pattern and replace is not None:
                name = re.sub(pattern, replace, name)

            # 生成序号
            num = str(start_num + i).zfill(padding)

            # 构建新文件名
            new_name = f"{prefix}{name}{num}{suffix}{ext}"
            new_path = path / new_name

            # 防止覆盖
            if new_path.exists() and new_path != f:
                print(f"[跳过] {f.name} -> {new_name} (目标已存在)")
                errors += 1
                continue

            if dry_run:
                print(f"[预览] {f.name} -> {new_name}")
            else:
                f.rename(new_path)
                print(f"{f.name} -> {new_name}")
            count += 1

        except Exception as e:
            print(f"[错误] {f.name}: {e}")
            errors += 1

    print(f"\n完成: 成功 {count} 个, 跳过/错误 {errors} 个")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="文件批量重命名工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./photos --prefix vacation_ --start 1
  %(prog)s ./docs --pattern " " --replace "_"
  %(prog)s ./data --suffix _backup --dry-run
        """
    )
    parser.add_argument("directory", help="目标目录路径")
    parser.add_argument("--prefix", default="", help="文件名前缀")
    parser.add_argument("--suffix", default="", help="文件名后缀（扩展名前）")
    parser.add_argument("--start", type=int, default=1, help="起始序号（默认1）")
    parser.add_argument("--padding", type=int, default=3, help="序号位数（默认3）")
    parser.add_argument("--pattern", help="正则匹配模式（需配合 --replace）")
    parser.add_argument("--replace", default="", help="正则替换文本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际重命名")

    args = parser.parse_args()
    exit(rename_files(
        args.directory, args.prefix, args.suffix,
        args.start, args.padding,
        args.pattern, args.replace, args.dry_run
    ))
