# -*- coding: utf-8 -*-
"""回合制战斗：伤害计算、暴击、经验与升级。"""

import random

from roguelike import config
from roguelike.entities import Fighter


def compute_damage(attacker_atk, defender_def, rng):
    """伤害 = 攻击 + 随机浮动 - 防御，下限保底。返回 (伤害, 是否暴击)。"""
    crit = rng.random() < config.CRIT_CHANCE
    dmg = attacker_atk + rng.randint(0, config.DMG_VARIANCE) - defender_def
    if crit:
        dmg = dmg * config.CRIT_MULT
    dmg = int(dmg)
    if dmg < config.MIN_DAMAGE:
        dmg = config.MIN_DAMAGE
    return dmg, crit


def attack(attacker, target, rng=None, attacker_power=None):
    """一次近战攻击。attacker/target 都是 Entity（有 fighter）。

    返回 (伤害, 是否暴击, 是否致死)。不处理死亡后果（由引擎处理）。
    """
    rng = rng or random
    if attacker_power is None:
        attacker_power = attacker.fighter.atk
    dmg, crit = compute_damage(attacker_power, target.fighter.defense, rng)
    target.fighter.hp -= dmg
    return dmg, crit, target.fighter.is_dead()


def gain_exp(fighter, amount, on_level_up=None):
    """加经验并处理升级（可能连升）。返回升了的级数。

    on_level_up(fighter, new_level) 供引擎回调（提示消息）。
    """
    if not isinstance(fighter, Fighter):
        raise TypeError("gain_exp 需要 Fighter")
    fighter.exp += amount
    levels = 0
    while fighter.exp >= fighter.exp_to_next:
        fighter.exp -= fighter.exp_to_next
        fighter.level += 1
        levels += 1
        fighter.max_hp += config.LEVEL_HP_GAIN
        fighter.hp = fighter.max_hp            # 升级回满
        fighter.atk += config.LEVEL_ATK_GAIN
        if fighter.level % 2 == 0:             # 每 2 级 +1 防
            fighter.defense += config.LEVEL_DEF_GAIN
        if on_level_up:
            on_level_up(fighter, fighter.level)
    return levels
