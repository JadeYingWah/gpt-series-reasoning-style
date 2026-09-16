#!/usr/bin/env python3
"""
文件批量重命名工具（生产级）

功能：
- 前缀/后缀添加
- 序号生成（可配置起始值和位数）
- 正则查找替换
- 预览模式（默认安全）
- 防覆盖保护
- 完整错误处理
- 递归选项

用法示例：
  python rename_tool.py ./photos --prefix vacation_ --start 1
  python rename_tool.py ./docs --pattern " " --replace "_"
  python rename_tool.py ./data --suffix _backup --apply
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class FileRenamer:
    """文件批量重命名处理器"""

    def __init__(self, directory: str, recursive: bool = False):
        self.path = Path(directory).resolve()
        self.recursive = recursive
        self.plan: List[Tuple[Path, Path]] = []
        self.errors: List[str] = []

    def collect_files(self) -> List[Path]:
        """收集待处理的文件列表"""
        if not self.path.is_dir():
            raise FileNotFoundError(f"目录不存在: {self.path}")

        if self.recursive:
            files = [f for f in self.path.rglob("*") if f.is_file()]
        else:
            files = [f for f in self.path.iterdir() if f.is_file()]

        return sorted(files)

    def build_plan(
        self,
        prefix: str = "",
        suffix: str = "",
        start_num: int = 1,
        padding: int = 3,
        pattern: Optional[str] = None,
        replace: str = "",
    ) -> None:
        """构建重命名计划（不实际执行）"""
        self.plan = []
        self.errors = []
        used_names = set()

        files = self.collect_files()

        for i, src in enumerate(files):
            try:
                stem = src.stem
                ext = src.suffix

                # 正则替换
                if pattern:
                    try:
                        stem = re.sub(pattern, replace, stem)
                    except re.error as e:
                        self.errors.append(f"正则错误 ({src.name}): {e}")
                        continue

                # 生成序号
                num = str(start_num + i).zfill(padding)

                # 构建新文件名
                new_stem = f"{prefix}{stem}{num}{suffix}"
                dst = src.with_name(f"{new_stem}{ext}")

                # 防覆盖检查
                if dst != src and dst.exists():
                    self.errors.append(f"跳过（目标已存在）: {src.name} -> {dst.name}")
                    continue

                # 防计划内重名
                if dst in used_names:
                    self.errors.append(f"跳过（计划内重名）: {src.name} -> {dst.name}")
                    continue

                used_names.add(dst)
                self.plan.append((src, dst))

            except Exception as e:
                self.errors.append(f"处理失败 ({src.name}): {e}")

    def execute(self, dry_run: bool = True) -> Tuple[int, int]:
        """执行重命名计划"""
        success = 0
        failed = 0

        for src, dst in self.plan:
            if dry_run:
                print(f"[预览] {src.name} -> {dst.name}")
                success += 1
                continue

            try:
                src.rename(dst)
                print(f"{src.name} -> {dst.name}")
                success += 1
            except PermissionError:
                print(f"[权限错误] {src.name}: 无权限访问")
                failed += 1
            except OSError as e:
                print(f"[系统错误] {src.name}: {e}")
                failed += 1
            except Exception as e:
                print(f"[未知错误] {src.name}: {e}")
                failed += 1

        return success, failed

    def print_summary(self, success: int, failed: int, dry_run: bool) -> None:
        """打印执行摘要"""
        mode = "预览" if dry_run else "执行"
        print(f"\n{'='*50}")
        print(f"{mode}完成: 成功 {success} 个, 失败 {failed} 个")
        if self.errors:
            print(f"警告/跳过 {len(self.errors)} 个:")
            for err in self.errors[:5]:
                print(f"  - {err}")
            if len(self.errors) > 5:
                print(f"  ... 还有 {len(self.errors) - 5} 条")
        print(f"{'='*50}")


def validate_args(args: argparse.Namespace) -> Optional[str]:
    """验证参数组合"""
    if args.pattern and not args.replace:
        return "使用 --pattern 时必须提供 --replace"
    if args.padding < 1:
        return "--padding 必须 >= 1"
    if args.start < 0:
        return "--start 必须 >= 0"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="文件批量重命名工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./photos --prefix vacation_ --start 1
  %(prog)s ./docs --pattern " " --replace "_"
  %(prog)s ./data --suffix _backup --apply
  %(prog)s ./project --recursive --prefix proj_

注意: 默认预览模式，加 --apply 才实际执行
        """,
    )

    parser.add_argument("directory", help="目标目录路径")
    parser.add_argument("--prefix", default="", help="文件名前缀")
    parser.add_argument("--suffix", default="", help="文件名后缀（扩展名前）")
    parser.add_argument("--start", type=int, default=1, help="起始序号（默认1）")
    parser.add_argument("--padding", type=int, default=3, help="序号位数（默认3）")
    parser.add_argument("--pattern", help="正则匹配模式（需配合 --replace）")
    parser.add_argument("--replace", default="", help="正则替换文本")
    parser.add_argument("--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("--apply", action="store_true", help="实际执行（默认预览模式）")

    args = parser.parse_args()

    # 参数验证
    error = validate_args(args)
    if error:
        parser.error(error)
        return 2

    try:
        renamer = FileRenamer(args.directory, recursive=args.recursive)
        renamer.build_plan(
            prefix=args.prefix,
            suffix=args.suffix,
            start_num=args.start,
            padding=args.padding,
            pattern=args.pattern,
            replace=args.replace,
        )

        dry_run = not args.apply
        success, failed = renamer.execute(dry_run=dry_run)
        renamer.print_summary(success, failed, dry_run)

        return 0 if failed == 0 and not renamer.errors else 1

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
