"""
OBJ模型验证脚本 - 实操验证工具
检查：语法、顶点/面计数、UV范围、法线归一化、面索引有效性、PBR参数范围
"""
import re
import sys
from pathlib import Path

def validate_obj(filepath):
    """验证OBJ文件的技术规范"""
    results = {
        'file': str(filepath),
        'vertices': 0,
        'faces': 0,
        'uvs': 0,
        'normals': 0,
        'triangle_count': 0,
        'quad_count': 0,
        'ngon_count': 0,
        'errors': [],
        'warnings': [],
        'uv_out_of_range': 0,
        'unnormalized_normals': 0,
        'invalid_face_indices': 0,
    }

    vertices = []
    uvs = []
    normals = []
    faces = []

    try:
        content = Path(filepath).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        results['errors'].append(f'无法读取文件: {e}')
        return results

    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd == 'v':
            if len(parts) < 4:
                results['errors'].append(f'行{line_num}: 顶点坐标不完整')
                continue
            try:
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                vertices.append((x, y, z))
            except ValueError:
                results['errors'].append(f'行{line_num}: 顶点坐标格式错误')

        elif cmd == 'vt':
            if len(parts) < 3:
                results['errors'].append(f'行{line_num}: UV坐标不完整')
                continue
            try:
                u, v = float(parts[1]), float(parts[2])
                uvs.append((u, v))
                if u < 0 or u > 1 or v < 0 or v > 1:
                    results['uv_out_of_range'] += 1
                    results['warnings'].append(f'行{line_num}: UV超出0-1范围 ({u},{v})')
            except ValueError:
                results['errors'].append(f'行{line_num}: UV坐标格式错误')

        elif cmd == 'vn':
            if len(parts) < 4:
                results['errors'].append(f'行{line_num}: 法线坐标不完整')
                continue
            try:
                nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                length = (nx**2 + ny**2 + nz**2) ** 0.5
                normals.append((nx, ny, nz))
                if abs(length - 1.0) > 0.01:
                    results['unnormalized_normals'] += 1
                    results['warnings'].append(f'行{line_num}: 法线未归一化 (长度={length:.3f})')
            except ValueError:
                results['errors'].append(f'行{line_num}: 法线坐标格式错误')

        elif cmd == 'f':
            if len(parts) < 4:
                results['errors'].append(f'行{line_num}: 面至少需要3个顶点')
                continue
            face_verts = len(parts) - 1
            faces.append(face_verts)
            if face_verts == 3:
                results['triangle_count'] += 1
            elif face_verts == 4:
                results['quad_count'] += 1
            else:
                results['ngon_count'] += 1
                results['warnings'].append(f'行{line_num}: n-gon ({face_verts}边形)')

            # 检查面索引有效性
            for i, vert_ref in enumerate(parts[1:], 1):
                # 格式: v/vt/vn 或 v//vn 或 v
                v_idx = int(vert_ref.split('/')[0])
                if abs(v_idx) > len(vertices):
                    results['invalid_face_indices'] += 1
                    results['errors'].append(f'行{line_num}: 面索引{v_idx}超出顶点范围({len(vertices)})')

    results['vertices'] = len(vertices)
    results['faces'] = len(faces)
    results['uvs'] = len(uvs)
    results['normals'] = len(normals)

    # 计算三角面总数（四边形按2个三角面计）
    total_tris = results['triangle_count'] + results['quad_count'] * 2 + results['ngon_count'] * 3
    results['estimated_triangles'] = total_tris

    return results

def validate_pbr_params(params):
    """验证PBR材质参数范围"""
    errors = []
    warnings = []

    for name, value, min_val, max_val in params:
        if value < min_val or value > max_val:
            errors.append(f'{name}={value} 超出范围 [{min_val}, {max_val}]')
        elif value == min_val or value == max_val:
            warnings.append(f'{name}={value} 处于边界值')

    return errors, warnings

def print_report(results):
    print('=' * 60)
    print('OBJ模型验证报告')
    print('=' * 60)
    print(f'文件: {results["file"]}')
    print(f'顶点数: {results["vertices"]}')
    print(f'面数: {results["faces"]} (三角:{results["triangle_count"]}, 四边:{results["quad_count"]}, n-gon:{results["ngon_count"]})')
    print(f'估算三角面总数: {results["estimated_triangles"]}')
    print(f'UV坐标数: {results["uvs"]} (超出0-1范围: {results["uv_out_of_range"]})')
    print(f'法线数: {results["normals"]} (未归一化: {results["unnormalized_normals"]})')
    print(f'无效面索引: {results["invalid_face_indices"]}')
    print()

    if results['errors']:
        print(f'错误 ({len(results["errors"])}):')
        for e in results['errors'][:10]:
            print(f'  ❌ {e}')
        if len(results['errors']) > 10:
            print(f'  ... 还有{len(results["errors"])-10}个错误')
    else:
        print('✅ 无错误')

    if results['warnings']:
        print(f'\n警告 ({len(results["warnings"])}):')
        for w in results['warnings'][:10]:
            print(f'  ⚠️  {w}')
        if len(results['warnings']) > 10:
            print(f'  ... 还有{len(results["warnings"])-10}个警告')
    else:
        print('✅ 无警告')

    print()
    passed = len(results['errors']) == 0
    print(f'验证结果: {"✅ 通过" if passed else "❌ 失败"}')
    return passed

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python validate_obj.py <obj文件路径>')
        sys.exit(1)

    results = validate_obj(sys.argv[1])
    passed = print_report(results)
    sys.exit(0 if passed else 1)
