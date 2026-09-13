"""
冒险游戏分支逻辑验证脚本 - 实操验证工具
检查：分支完整性、死胡同、状态一致性、结局可达性、选择有意义性
"""
import json
from pathlib import Path

def validate_adventure(structure):
    """验证冒险游戏的分支逻辑"""
    results = {
        'scenes': 0,
        'choices': 0,
        'endings': 0,
        'dead_ends': [],
        'unreachable_scenes': [],
        'unreachable_endings': [],
        'meaningless_choices': [],
        'state_inconsistencies': [],
        'errors': [],
        'warnings': [],
    }

    scenes = structure.get('scenes', {})
    endings = structure.get('endings', {})
    start = structure.get('start_scene')

    results['scenes'] = len(scenes)
    results['endings'] = len(endings)

    # 1. 检查每个场景的选择是否都有目标
    for scene_id, scene in scenes.items():
        choices = scene.get('choices', [])
        results['choices'] += len(choices)

        if not choices and scene_id not in endings:
            results['dead_ends'].append(scene_id)
            results['errors'].append(f'场景 {scene_id} 没有选择且不是结局')

        for i, choice in enumerate(choices):
            target = choice.get('target')
            if not target:
                results['errors'].append(f'场景 {scene_id} 选择{i+1} 没有目标场景')
            elif target not in scenes and target not in endings:
                results['errors'].append(f'场景 {scene_id} 选择{i+1} 目标 {target} 不存在')

            # 检查选择是否有不同后果（有意义的选择）
            if not choice.get('effects') and not choice.get('condition'):
                results['meaningless_choices'].append(f'{scene_id}:选择{i+1}')
                results['warnings'].append(f'场景 {scene_id} 选择{i+1} 没有效果或条件，可能是无意义选择')

    # 2. 检查结局可达性（从起点BFS）
    if start:
        visited = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            scene = scenes.get(current, {})
            for choice in scene.get('choices', []):
                target = choice.get('target')
                if target and target not in visited:
                    queue.append(target)

        # 检查不可达场景
        for scene_id in scenes:
            if scene_id not in visited:
                results['unreachable_scenes'].append(scene_id)
                results['warnings'].append(f'场景 {scene_id} 从起点不可达')

        # 检查不可达结局
        for ending_id in endings:
            if ending_id not in visited:
                results['unreachable_endings'].append(ending_id)
                results['warnings'].append(f'结局 {ending_id} 从起点不可达')

    # 3. 检查状态一致性（物品获取和使用）
    all_items = set()
    used_items = set()
    for scene_id, scene in scenes.items():
        for choice in scene.get('choices', []):
            effects = choice.get('effects', {})
            if 'add_item' in effects:
                all_items.add(effects['add_item'])
            if 'remove_item' in effects:
                used_items.add(effects['remove_item'])
            condition = choice.get('condition', {})
            if 'require_item' in condition:
                used_items.add(condition['require_item'])

    for item in used_items:
        if item not in all_items:
            results['state_inconsistencies'].append(item)
            results['errors'].append(f'物品 {item} 被使用/要求但从未被获取')

    return results

def print_report(results):
    print('=' * 60)
    print('冒险游戏分支逻辑验证报告')
    print('=' * 60)
    print(f'场景数: {results["scenes"]}')
    print(f'选择数: {results["choices"]}')
    print(f'结局数: {results["endings"]}')
    print(f'死胡同: {len(results["dead_ends"])}')
    print(f'不可达场景: {len(results["unreachable_scenes"])}')
    print(f'不可达结局: {len(results["unreachable_endings"])}')
    print(f'无意义选择: {len(results["meaningless_choices"])}')
    print(f'状态不一致: {len(results["state_inconsistencies"])}')
    print()

    if results['errors']:
        print(f'错误 ({len(results["errors"])}):')
        for e in results['errors']:
            print(f'  ❌ {e}')
    else:
        print('✅ 无错误')

    if results['warnings']:
        print(f'\n警告 ({len(results["warnings"])}):')
        for w in results['warnings']:
            print(f'  ⚠️  {w}')
    else:
        print('✅ 无警告')

    print()
    passed = len(results['errors']) == 0
    print(f'验证结果: {"✅ 通过" if passed else "❌ 失败"}')
    return passed

# 定义冒险游戏结构（用于验证）
ADVENTURE_STRUCTURE = {
    'start_scene': 'control_room',
    'scenes': {
        'control_room': {
            'choices': [
                {'text': '检查站长', 'target': 'corridor', 'effects': {'add_item': 'keycard', 'time': -2}},
                {'text': '打开工具箱', 'target': 'corridor', 'effects': {'add_item': 'wrench', 'add_item2': 'flashlight', 'time': -1}},
                {'text': '直接冲向走廊', 'target': 'corridor', 'effects': {'health': -20, 'time': 0}},
            ]
        },
        'corridor': {
            'choices': [
                {'text': '去引擎室', 'target': 'engine_room', 'effects': {'time': -3}},
                {'text': '去医疗舱', 'target': 'medical_bay', 'effects': {'time': -3}},
                {'text': '清理碎片', 'target': 'escape_pod', 'condition': {'require_item': 'wrench'}, 'effects': {'time': -5}},
            ]
        },
        'engine_room': {
            'choices': [
                {'text': '启动发电机', 'target': 'corridor2', 'condition': {'require_item': 'wrench'}, 'effects': {'time': -2, 'oxygen': 10}},
                {'text': '离开', 'target': 'corridor2', 'effects': {'time': -1}},
            ]
        },
        'medical_bay': {
            'choices': [
                {'text': '拿氧气罐', 'target': 'corridor2', 'effects': {'add_item': 'oxygen_tank', 'time': -1}},
                {'text': '拿医疗包', 'target': 'corridor2', 'effects': {'add_item': 'medkit', 'time': -1}},
                {'text': '两个都拿', 'target': 'corridor2', 'effects': {'add_item': 'oxygen_tank', 'add_item2': 'medkit', 'time': -2}},
            ]
        },
        'corridor2': {
            'choices': [
                {'text': '前往居住区', 'target': 'habitat', 'effects': {'time': -2}},
                {'text': '直接去逃生舱', 'target': 'escape_pod', 'effects': {'time': -3}},
            ]
        },
        'habitat': {
            'choices': [
                {'text': '救人', 'target': 'escape_pod', 'effects': {'allies': 2, 'time': -8}},
                {'text': '继续前进', 'target': 'escape_pod', 'effects': {'allies': 0, 'time': -1}},
                {'text': '留下氧气罐', 'target': 'escape_pod', 'condition': {'require_item': 'oxygen_tank'}, 'effects': {'allies': 1, 'remove_item': 'oxygen_tank', 'time': 0}},
            ]
        },
        'escape_pod': {
            'choices': [
                {'text': '输入密码', 'target': 'ending_check', 'condition': {'require_item': 'password'}, 'effects': {}},
                {'text': '回去找线索', 'target': 'control_room2', 'effects': {'time': -4}},
                {'text': '暴力破解', 'target': 'ending_self_destruct', 'effects': {'health': -30, 'time': -10}},
            ]
        },
        'ending_check': {
            'choices': [
                {'text': '[判定] 氧气充足且救了人', 'target': 'ending_perfect', 'condition': {'oxygen_min': 1, 'allies_min': 1}, 'effects': {}},
                {'text': '[判定] 氧气充足但没救人', 'target': 'ending_alone', 'condition': {'oxygen_min': 1, 'allies_max': 0}, 'effects': {}},
                {'text': '[判定] 氧气耗尽', 'target': 'ending_breathless', 'condition': {'oxygen_max': 0}, 'effects': {}},
            ]
        },
        'control_room2': {
            'choices': [
                {'text': '找到密码', 'target': 'escape_pod', 'effects': {'add_item': 'password', 'time': -2}},
            ]
        },
    },
    'endings': {
        'ending_perfect': {'type': 'good', 'condition': 'oxygen>0 and allies>=1'},
        'ending_alone': {'type': 'neutral', 'condition': 'oxygen>0 and allies=0'},
        'ending_breathless': {'type': 'bad', 'condition': 'oxygen<=0'},
        'ending_self_destruct': {'type': 'bad', 'condition': '暴力破解失败'},
    }
}

if __name__ == '__main__':
    results = validate_adventure(ADVENTURE_STRUCTURE)
    passed = print_report(results)
