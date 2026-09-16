"""回合制战斗结算：伤害公式、暴击、玩家攻击与敌人反击。"""

from __future__ import annotations

import random

from . import config


def roll_damage(
    rng: random.Random, atk: int, dfn: int, force_crit: bool = False
) -> tuple[int, bool]:
    """伤害 = max(1, 攻击 - 防御 + rand(-1..2))，暴击则翻倍。

    返回 (伤害, 是否暴击)。
    """
    base = max(1, atk - dfn + rng.randint(-1, 2))
    crit = force_crit or (rng.random() < config.CRIT_CHANCE)
    if crit:
        base *= 2
    return base, crit


def player_attack(game, enemy) -> None:
    """玩家攻击一只敌人；击杀时结算掉落与经验。攻击会惊醒沉睡的敌人。"""
    if enemy.state != "chase":
        enemy.state = "chase"
        game.push(f"你惊醒了{enemy.name}！")
    dmg, crit = roll_damage(game.rng, game.player.atk, enemy.dfn)
    enemy.hp -= dmg
    game.push(
        f"你攻击{enemy.name}，造成 {dmg} 点伤害。"
        + ("会心一击！" if crit else "")
    )
    if enemy.hp <= 0:
        game.kill_enemy(enemy)


def enemy_attack(game, enemy) -> None:
    """敌人攻击玩家；魔王每第 3 次攻击必定蓄力重击。"""
    enemy.attack_count += 1
    force_crit = enemy.boss and (enemy.attack_count % 3 == 0)
    dmg, crit = roll_damage(game.rng, enemy.atk, game.player.dfn, force_crit)
    game.player.hp -= dmg
    if enemy.boss and force_crit:
        game.push(f"{enemy.name}释放蓄力重击！")
    game.push(
        f"{enemy.name}攻击你，造成 {dmg} 点伤害。"
        + ("会心一击！" if crit else "")
    )
    if game.player.hp <= 0:
        game.player.hp = 0
        if not game.over:
            game.over = True
            game.push("你倒在了黑暗中…… 冒险到此结束。")
