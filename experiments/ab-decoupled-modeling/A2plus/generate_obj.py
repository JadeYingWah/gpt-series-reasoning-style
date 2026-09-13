"""生成可靠的能量核心OBJ文件（细分八面体）"""
import math

def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    return (v[0]/l, v[1]/l, v[2]/l)

def midpoint(v1, v2):
    return ((v1[0]+v2[0])/2, (v1[1]+v2[1])/2, (v1[2]+v2[2])/2)

# 初始八面体
verts = [
    (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)
]
faces = [
    (0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
    (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)
]

# 细分2级
for _ in range(2):
    new_verts = list(verts)
    new_faces = []
    mid_cache = {}
    def get_mid(i, j):
        key = (min(i,j), max(i,j))
        if key not in mid_cache:
            mid = normalize(midpoint(verts[i], verts[j]))
            mid_cache[key] = len(new_verts)
            new_verts.append(mid)
        return mid_cache[key]
    for a, b, c in faces:
        ab = get_mid(a, b)
        bc = get_mid(b, c)
        ca = get_mid(c, a)
        new_faces.extend([(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)])
    verts = new_verts
    faces = new_faces

# 生成OBJ
lines = ["# Energy Core - Subdivided Octahedron", f"# Vertices: {len(verts)}, Faces: {len(faces)}", ""]
for v in verts:
    lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
lines.append("")
# 法线（顶点法线=位置，因为是单位球）
for v in verts:
    lines.append(f"vn {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
lines.append("")
# UV（简单球面映射）
for v in verts:
    u = 0.5 + math.atan2(v[2], v[0]) / (2 * math.pi)
    v_coord = 0.5 - math.asin(v[1]) / math.pi
    lines.append(f"vt {u:.6f} {v_coord:.6f}")
lines.append("")
# 面（1-indexed）
for a, b, c in faces:
    lines.append(f"f {a+1}/{a+1}/{a+1} {b+1}/{b+1}/{b+1} {c+1}/{c+1}/{c+1}")

with open(r"<实验根目录>\ab-decoupled-modeling\A2plus\energy_core.obj", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"生成完成: {len(verts)}顶点, {len(faces)}面")
