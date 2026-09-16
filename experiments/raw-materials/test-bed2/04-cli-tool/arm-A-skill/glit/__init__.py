# -*- coding: utf-8 -*-
"""glit — 一个 Git-lite 版本控制工具（教学/实验用途）。

自定义对象存储格式：
    header = b"GLIT" + version(1B) + type(1B) + payload_len(4B big-endian)
    full   = header + payload
    sha    = sha1(full).hexdigest()
    stored = zlib.compress(full)
    落盘路径：objects/<sha[:2]>/<sha[2:]>

对象类型：
    1 = blob   （文件原始字节）
    2 = tree   （目录快照，JSON）
    3 = commit （提交元数据，JSON）
"""

__version__ = "1.0.0"


class GlitError(Exception):
    """glit 的统一业务错误。CLI 层捕获后打印到 stderr 并以退出码 1 退出。"""
