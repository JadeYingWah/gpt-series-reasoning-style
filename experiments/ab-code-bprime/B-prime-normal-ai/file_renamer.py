#!/usr/bin/env python3
"""批量文件重命名工具 - 支持正则替换、前缀/后缀、序号、dry-run模式"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(__name__)


def build_new_name(old_name, args, index):
    """根据参数构建新文件名"""
    stem = Path(old_name).stem
    suffix = Path(old_name).suffix

    if args.mode == "replace":
        stem = stem.replace(args.pattern, args.replacement)
    elif args.mode == "regex":
        stem = re.sub(args.pattern, args.replacement, stem)
    elif args.mode == "prefix":
        stem = args.prefix + stem
    elif args.mode == "suffix":
        stem = stem + args.suffix
    elif args.mode == "sequence":
        stem = f"{args.prefix}{index:0{args.padding}d}"

    return stem + suffix


def collect_files(directory, pattern=None, recursive=False):
    """收集待处理文件"""
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")
    if not path.is_dir():
        raise NotADirectoryError(f"不是目录: {directory}")

    files = []
    if recursive:
        iterator = path.rglob("*")
    else:
        iterator = path.iterdir()

    for f in sorted(iterator):
        if f.is_file():
            if pattern is None or re.search(pattern, f.name):
                files.append(f)
    return files


def execute_rename(files, args, logger):
    """执行重命名，返回(成功数, 失败数, 操作列表)"""
    success = 0
    failed = 0
    operations = []

    for i, old_path in enumerate(files, 1):
        new_name = build_new_name(old_path.name, args, i)
        new_path = old_path.parent / new_name

        if new_path == old_path:
            logger.debug(f"跳过（无变化）: {old_path.name}")
            continue

        if new_path.exists() and not args.overwrite:
            logger.warning(f"跳过（目标已存在）: {old_path.name} -> {new_name}")
            failed += 1
            continue

        if args.dry_run:
            logger.info(f"[dry-run] {old_path.name} -> {new_name}")
            operations.append((str(old_path), str(new_path), "planned"))
            success += 1
        else:
            try:
                old_path.rename(new_path)
                logger.info(f"重命名: {old_path.name} -> {new_name}")
                operations.append((str(old_path), str(new_path), "done"))
                success += 1
            except PermissionError:
                logger.error(f"权限不足: {old_path}")
                failed += 1
            except OSError as e:
                logger.error(f"重命名失败 {old_path}: {e}")
                failed += 1

    return success, failed, operations


def main():
    parser = argparse.ArgumentParser(
        description="批量文件重命名工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./photos --mode replace --pattern "IMG" --replacement "photo" --dry-run
  %(prog)s ./docs --mode regex --pattern "(\d+)" --replacement "doc_\\1"
  %(prog)s ./files --mode sequence --prefix "file_" --padding 3
        """,
    )
    parser.add_argument("directory", help="目标目录")
    parser.add_argument("--mode", choices=["replace", "regex", "prefix", "suffix", "sequence"],
                        default="replace", help="重命名模式")
    parser.add_argument("--pattern", help="匹配模式（replace/regex模式）")
    parser.add_argument("--replacement", help="替换文本")
    parser.add_argument("--prefix", help="前缀（prefix/sequence模式）")
    parser.add_argument("--suffix", help="后缀（suffix模式）")
    parser.add_argument("--padding", type=int, default=3, help="序号补零位数（sequence模式）")
    parser.add_argument("--filter", help="文件名过滤正则")
    parser.add_argument("--recursive", action="store_true", help="递归子目录")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不实际修改")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    # 参数校验
    if args.mode in ("replace", "regex") and not args.pattern:
        parser.error(f"{args.mode}模式需要 --pattern")
    if args.mode == "prefix" and not args.prefix:
        parser.error("prefix模式需要 --prefix")
    if args.mode == "suffix" and not args.suffix:
        parser.error("suffix模式需要 --suffix")
    if args.mode == "sequence" and not args.prefix:
        parser.error("sequence模式需要 --prefix")

    try:
        files = collect_files(args.directory, args.filter, args.recursive)
    except (FileNotFoundError, NotADirectoryError) as e:
        logger.error(str(e))
        sys.exit(1)

    if not files:
        logger.warning("没有找到匹配的文件")
        sys.exit(0)

    logger.info(f"找到 {len(files)} 个文件")
    success, failed, operations = execute_rename(files, args, logger)

    logger.info(f"完成: 成功 {success}, 失败 {failed}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
