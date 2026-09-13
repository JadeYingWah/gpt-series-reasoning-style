"""建模类验证脚本 - A2+配置"""
import re
import math

OBJ = r"<实验根目录>\ab-decoupled-modeling\A2plus\energy_core.obj"

def parse_obj(path):
    verts, normals, uvs, faces = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("v "):
                parts = line.split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("vn "):
                parts = line.split()
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("vt "):
                parts = line.split()
                uvs.append((float(parts[1]), float(parts[2])))
            elif line.startswith("f "):
                faces.append(line)
    return verts, normals, uvs, faces

def check_vertex_count(verts):
    return 50 <= len(verts) <= 200, f"{len(verts)}个顶点（要求50-200）"

def check_face_count(faces):
    return 30 <= len(faces) <= 150, f"{len(faces)}个面（要求30-150）"

def check_normal_normalized(normals):
    """检查法线是否归一化（长度≈1，容差0.01）"""
    bad = []
    for i, (x, y, z) in enumerate(normals):
        length = math.sqrt(x*x + y*y + z*z)
        if abs(length - 1.0) > 0.01:
            bad.append((i+1, length))
    return len(bad) == 0, f"{len(normals)}组法线，{len(bad)}组未归一化"

def check_uv_range(uvs):
    """检查UV坐标是否在0-1范围内"""
    bad = []
    for i, (u, v) in enumerate(uvs):
        if not (0 <= u <= 1 and 0 <= v <= 1):
            bad.append((i+1, u, v))
    return len(bad) == 0, f"{len(uvs)}组UV，{len(bad)}组越界"

def check_face_indices(faces, vert_count, normal_count, uv_count):
    """检查面引用的索引是否有效"""
    bad = []
    for i, face in enumerate(faces):
        refs = re.findall(r"(\d+)/?(\d*)/?(\d*)", face)
        for v_idx, vt_idx, vn_idx in refs:
            v = int(v_idx)
            if v < 1 or v > vert_count:
                bad.append((i+1, f"顶点索引{v}越界"))
            if vn_idx and int(vn_idx) > normal_count:
                bad.append((i+1, f"法线索引{vn_idx}越界"))
            if vt_idx and int(vt_idx) > uv_count:
                bad.append((i+1, f"UV索引{vt_idx}越界"))
    return len(bad) == 0, f"{len(faces)}个面，{len(bad)}个索引错误"

def check_triangles(faces):
    """检查是否所有面都是三角形"""
    non_tri = []
    for i, face in enumerate(faces):
        refs = re.findall(r"\d+/\d*/\d*", face)
        if len(refs) != 3:
            non_tri.append((i+1, len(refs)))
    return len(non_tri) == 0, f"{len(faces)}个面，{len(non_tri)}个非三角形"

if __name__ == "__main__":
    verts, normals, uvs, faces = parse_obj(OBJ)
    print("=== 建模类验证 ===")
    checks = [
        ("顶点数", check_vertex_count(verts)),
        ("面数", check_face_count(faces)),
        ("三角形", check_triangles(faces)),
        ("法线归一化", check_normal_normalized(normals)),
        ("UV范围", check_uv_range(uvs)),
        ("索引有效", check_face_indices(faces, len(verts), len(normals), len(uvs))),
    ]
    allok = True
    for name, (ok, msg) in checks:
        allok = allok and ok
        print(f"  {'PASS' if ok else 'FAIL'} - {name}: {msg}")
    print(f"\n总体: {'全部通过' if allok else '存在问题'}")
