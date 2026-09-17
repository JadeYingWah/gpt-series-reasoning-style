# -*- coding: utf-8 -*-
"""
WutheringWavesDmgCalc — 计算引擎
================================
纯数学函数，零 GUI 依赖。供主程序和自动化测试共同 import。

提取自: WWDmgCalc.py v1.6
提取日期: 2026-06-01

包含:
  - 游戏常量（元素、技能、效应、乘区关键词）
  - 7 个乘区计算公式
  - 筛选匹配逻辑
  - 完整伤害公式
"""

# ============================================================
# 游戏常量
# ============================================================

ELEMENTS = ["(无)", "冷凝", "热熔", "气动", "导电", "衍射", "湮灭"]
SKILL_TYPES = ["(无)", "普攻", "重击", "共鸣技能", "共鸣解放", "变奏技能", "声骸技能"]
EFFECTS = ["(无)", "光噪", "风蚀", "虚湮", "聚爆", "霜渐", "电磁"]

ELEMENT_NAMES_SET = {"冷凝", "热熔", "气动", "导电", "衍射", "湮灭"}
SKILL_TYPE_NAMES_SET = {"普攻", "重击", "共鸣技能", "共鸣解放", "变奏技能", "声骸技能"}
EFFECT_NAMES_SET = {"光噪", "风蚀", "虚湮", "聚爆", "霜渐", "电磁"}

# 防御减伤词条名称（仅通用，技能专用变体见 SKILL_DEF_PEN）
DEFENSE_ITEM_NAMES = {
    "无视防御", "忽视防御", "减少防御",
}

# 抗性词条名称
# 技能专用无视防御（仅匹配对应技能时生效，不归入通用防御池）
SKILL_DEF_PENETRATION = {
    "普攻无视防御", "重击无视防御",
    "共鸣技能无视防御", "共鸣解放无视防御",
    "变奏技能无视防御", "声骸技能无视防御",
}

# 技能名 → 无视防御词条前缀 映射
_SKILL_DEF_PEN_MAP = {
    "普攻": ("普攻无视防御",),
    "重击": ("重击无视防御",),
    "共鸣技能": ("共鸣技能无视防御",),
    "共鸣解放": ("共鸣解放无视防御",),
    "变奏技能": ("变奏技能无视防御",),
    "声骸技能": ("声骸技能无视防御",),
}

def get_def_pen_skill_type(name):
    """判断「技能专用无视防御」词条归属于哪个技能类型。

    Args:
        name: 词条名称（如 "普攻无视防御"、"共鸣解放无视防御"）

    Returns:
        str: 技能类型名（"普攻"/"重击"/"共鸣技能"/"共鸣解放"/"变奏技能"/"声骸技能"）
        None: 不属于任何技能专用类型（通用词条）

    用途:
        - 防御页 recalc() 按技能类型分类词条到 7 张表格
        - is_defense_item() 排除技能专用变体避免重复匹配
        - 计算结果页根据卡片技能类型获取对应防御乘区
    """
    for skill_type, prefixes in _SKILL_DEF_PEN_MAP.items():
        if name in prefixes:
            return skill_type
    return None

RESISTANCE_ITEM_NAMES = {
    "冷凝抗性无视", "热熔抗性无视", "气动抗性无视",
    "导电抗性无视", "衍射抗性无视", "湮灭抗性无视",
    "冷凝抗性减少", "热熔抗性减少", "气动抗性减少",
    "导电抗性减少", "衍射抗性减少", "湮灭抗性减少",
    "全属性抗性减少",
}

RESISTANCE_TYPES = [
    "冷凝抗性", "热熔抗性", "气动抗性", "导电抗性", "衍射抗性", "湮灭抗性"
]

# 乘区分类关键词
BONUS_SUFFIX = ["伤害加成", "伤害提升"]
DEEPEN_SUFFIX = "加深"
CRIT_RATE_KEYWORDS = {"暴击率"}
CRIT_DMG_KEYWORDS = {"暴击伤害", "暴击伤害加成", "暴伤", "暴傷"}

# 基础值分类
ATK_PCT_NAMES = {"攻击力加成", "攻击力", "攻击"}
ATK_FLAT_NAMES = {"固定攻击"}

# 抗性预设
RESISTANCE_PRESETS = {
    "world": {"base": 10, "boost": 30},
    "tower": {"base": 20, "boost": 40},
    "holo":  {"base": 10, "boost": 70},
}


# ============================================================
# 筛选匹配
# ============================================================

def matches_filter(item_name, selected_element, selected_skill, selected_effect):
    """检查词条是否满足元素/技能/效应筛选条件。

    来源: WWDmgCalc.py _matches_filter() (line ~6432)

    规则:
    - 筛选为 None 时：排除带特定标签的词条，仅保留通用词条
    - 筛选为具体值时：保留匹配该值的词条 + 通用词条
    """
    name = item_name
    for prefix in ["[声骸]主词条-", "[声骸]固定词条-", "[声骸]副词条-"]:
        if name.startswith(prefix):
            name = name[len(prefix):]

    for e in ELEMENT_NAMES_SET:
        if e in name:
            if not selected_element or e != selected_element:
                return False
            break

    for s in SKILL_TYPE_NAMES_SET:
        if s in name:
            if not selected_skill or s != selected_skill:
                return False
            break

    for ef in EFFECT_NAMES_SET:
        if ef in name:
            if not selected_effect or ef != selected_effect:
                return False
            break

    return True


def is_defense_item(name):
    """判断词条是否属于防御减伤类（含技能专用变体）。

    Returns True 的条件（满足任一）:
        1. 名称包含 "无视防御"/"忽视防御"/"减少防御" 任一子串
        2. 名称在 DEFENSE_ITEM_NAMES 中精确匹配

    用途:
        - CombinedEntryPage._navigate_to_summary(): 决定"查看总结"跳转目标
        - EnemyDefensePage.recalc(): 收集防御词条
        - classify_item_category(): 词条→"defense" 分类路由
    """
    for kw in ("无视防御", "忽视防御", "减少防御"):
        if kw in name:
            return True
    return name in DEFENSE_ITEM_NAMES


def is_resistance_item(name):
    """判断词条是否属于抗性类，返回匹配的抗性类型（或 None）"""
    # 先尝试精确匹配
    if name in RESISTANCE_ITEM_NAMES:
        if name == "全属性抗性减少":
            return list(RESISTANCE_TYPES)
        for t in RESISTANCE_TYPES:
            if name.startswith(t):
                return [t]
        return []
    # 模糊匹配：含抗性关键词
    for kw in ("抗性无视", "抗性减少"):
        if kw in name:
            for t in RESISTANCE_TYPES:
                if name.startswith(t):
                    return [t]
            return list(RESISTANCE_TYPES)  # 全属性
    return []


def classify_item_category(name):
    """根据词条名称判断所属乘区分类。

    Returns: "crit" | "deepen" | "bonus" | "defense" | "resistance" | "base" | "other"
    """
    if any(kw in name for kw in CRIT_DMG_KEYWORDS | CRIT_RATE_KEYWORDS):
        return "crit"
    if DEEPEN_SUFFIX in name:
        return "deepen"
    if any(s in name for s in BONUS_SUFFIX):
        return "bonus"
    if is_defense_item(name):
        return "defense"
    if is_resistance_item(name):
        return "resistance"
    if any(kw in name for kw in ATK_PCT_NAMES | ATK_FLAT_NAMES):
        return "base"
    return "other"


# ============================================================
# 核心伤害公式
# ============================================================

def calc_defense_zone(char_level, enemy_level, total_ignore=0.0, total_reduce=0.0):
    """计算防御乘区。

    来源: EnemyDefensePage.recalc()

    敌方基础防御 = 792 + 8 × 敌人等级
    敌方最终防御 = 敌方基础防御 × (1 − 无视防御) × (1 − 忽视/减少防御)
    防御乘区 = (800 + 8 × 角色等级) / (敌方最终防御 + 800 + 8 × 角色等级)
    """
    total_ignore = min(total_ignore, 1.0)
    total_reduce = min(total_reduce, 1.0)
    enemy_base_def = 792 + 8 * enemy_level
    enemy_final_def = enemy_base_def * (1.0 - total_ignore) * (1.0 - total_reduce)
    return (800 + 8 * char_level) / (enemy_final_def + 800 + 8 * char_level)


def calc_enemy_base_def(enemy_level):
    """计算敌方基础防御: 792 + 8 × 等级"""
    return 792 + 8 * enemy_level


def calc_resistance_zone(base_res, boost_pct=0.0, reduce_pct=0.0, ext_reduce=0.0):
    """计算单个元素的抗性乘区。

    来源: EnemyResistancePage._recalc() (line ~4915)

    最终抗性 = 基础抗性 × (1 + 抗性提升/100) − 抗性减少 − 外部减免
    抗性乘区:
      最终抗性 ≥ 0: 乘区 = 1 − 最终抗性/100
      最终抗性 < 0: 乘区 = 1 − 最终抗性/200（负抗性收益减半）
    """
    final_res = base_res * (1.0 + boost_pct / 100.0) - reduce_pct - ext_reduce
    if final_res < 0:
        return 1.0 - final_res / 200.0  # 负抗性收益减半
    return 1.0 - final_res / 100.0


def calc_indep_zone(groups):
    """计算独立乘区。

    来源: IndepZonePage.recalc() (line ~6382)

    每组: group_factor = 1.0 + sum(values) / 100
    总乘区: product of all group_factors

    Args:
        groups: list of list of values（每个内部列表是一个组的所有数值百分比）
    Returns:
        (total_zone, group_factors) where group_factors is [(name, factor), ...]
    """
    zone = 1.0
    factors = []
    for i, values in enumerate(groups):
        total = sum(values)
        gf = 1.0 + total / 100.0
        factors.append((f"group_{i}", gf))
        zone *= gf
    return zone, factors


def calc_base_zone(base_value, weapon_base, total_pct, total_flat):
    """计算基础乘区（攻击/生命/防御通用）。

    来源: ResultPage.compute() (line ~8217)

    基础乘区 = (角色基础 + 武器基础) × (1 + 百分比加成/100) + 固定值
    """
    return (base_value + weapon_base) * (1.0 + total_pct / 100.0) + total_flat


def calc_bonus_zone(total_bonus):
    """计算加成乘区: 1 + 总伤害加成/100"""
    return 1.0 + total_bonus / 100.0


def calc_deepen_zone(total_deepen):
    """计算加深乘区: 1 + 总伤害加深/100"""
    return 1.0 + total_deepen / 100.0


def calc_crit_zone(total_crit_dmg):
    """计算暴击乘区: (150 + 暴击伤害加成) / 100"""
    return (150.0 + total_crit_dmg) / 100.0


def calc_crit_rate(total_crit_rate):
    """计算最终暴击率: 5 + 暴击率加成"""
    return 5.0 + total_crit_rate


def calc_mult_zone(base_mult, mult_increase, mult_boosts):
    """计算倍率乘区。

    来源: ResultPage.compute() (line ~8256)

    公式: (基础倍率 + 倍率增加) × Π(1 + 倍率增幅/100)
    """
    zone = base_mult + mult_increase
    for bv in mult_boosts:
        zone *= (1.0 + bv / 100.0)
    return zone


def calc_final_damage(base_zone, bonus_zone, deepen_zone, crit_zone,
                      def_zone, res_zone, indep_zone, mult_zone):
    """计算最终伤害（暴击 + 非暴击）。

    来源: ResultPage.compute() (line ~8260)

    最终伤害 = base × bonus × deepen × def × res × indep × mult / 100
    暴击伤害 = 最终伤害 × crit_zone
    """
    base_dmg = (base_zone * bonus_zone * deepen_zone *
                def_zone * res_zone * indep_zone * mult_zone) / 100.0
    final_crit = base_dmg * crit_zone
    return base_dmg, final_crit


# ============================================================
# 全流程计算（一次调用得到所有乘区）
# ============================================================

def compute_all_zones(base_value, weapon_base, total_pct, total_flat,
                      total_bonus, total_deepen, total_crit_rate, total_crit_dmg,
                      char_level, enemy_level, total_ignore, total_reduce,
                      base_res, res_boost, res_reduce, res_ext_reduce,
                      indep_groups, base_mult, mult_increase, mult_boosts):
    """一次性计算所有乘区和最终伤害。

    这是把各乘区串联起来的便捷函数，供 ResultPage.compute() 直接调用。
    返回一个字典，包含全部中间值和最终结果。
    """
    base_zone = calc_base_zone(base_value, weapon_base, total_pct, total_flat)
    bonus_zone = calc_bonus_zone(total_bonus)
    deepen_zone = calc_deepen_zone(total_deepen)
    crit_rate = calc_crit_rate(total_crit_rate)
    crit_zone = calc_crit_zone(total_crit_dmg)
    def_zone = calc_defense_zone(char_level, enemy_level, total_ignore, total_reduce)
    res_zone = calc_resistance_zone(base_res, res_boost, res_reduce, res_ext_reduce)
    indep_zone, indep_factors = calc_indep_zone(indep_groups)
    mult_zone = calc_mult_zone(base_mult, mult_increase, mult_boosts)

    base_dmg, final_crit = calc_final_damage(
        base_zone, bonus_zone, deepen_zone, crit_zone,
        def_zone, res_zone, indep_zone, mult_zone,
    )

    return {
        "base_zone": base_zone, "bonus_zone": bonus_zone,
        "deepen_zone": deepen_zone, "crit_zone": crit_zone,
        "crit_rate": crit_rate, "def_zone": def_zone,
        "res_zone": res_zone, "indep_zone": indep_zone,
        "indep_factors": indep_factors, "mult_zone": mult_zone,
        "final_no_crit": base_dmg, "final_crit": final_crit,
    }
