# -*- coding: utf-8 -*-
"""存档读档：JSON 文件读写与版本校验。游戏状态序列化由 engine.Game 负责。"""

import json
import os
import time

from roguelike import config

SAVE_VERSION = 1


def save_game(state_dict, path=None):
    """把游戏状态 dict 写入存档文件。返回存档路径。"""
    path = path or config.SAVE_FILE
    payload = {
        "version": SAVE_VERSION,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "state": state_dict,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)          # 原子替换，避免写一半损坏
    return path


def load_game(path=None):
    """读取存档。返回 state dict；文件不存在/损坏/版本不符返回 None。"""
    path = path or config.SAVE_FILE
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict) or payload.get("version") != SAVE_VERSION:
        return None
    return payload.get("state")


def has_save(path=None):
    return os.path.exists(path or config.SAVE_FILE)


def rng_state_to_json(state):
    """random.Random.getstate() → 可 JSON 化结构。"""
    version, internal, gauss = state
    return [version, list(internal), gauss]


def rng_state_from_json(data):
    """还原 random.Random 可用的 state tuple。"""
    version, internal, gauss = data
    return (version, tuple(internal), gauss)
