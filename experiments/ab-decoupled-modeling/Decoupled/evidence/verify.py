"""Modeling verification - Decoupled"""
import re, math

OBJ = r"<实验根目录>\ab-decoupled-modeling\Decoupled\energy_core.obj"

def parse(path):
    v, vn, vt, f = [], [], [], []
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line.startswith("v "):
                p = line.split(); v.append((float(p[1]),float(p[2]),float(p[3])))
            elif line.startswith("vn "):
                p = line.split(); vn.append((float(p[1]),float(p[2]),float(p[3])))
            elif line.startswith("vt "):
                p = line.split(); vt.append((float(p[1]),float(p[2])))
            elif line.startswith("f "):
                f.append(line)
    return v, vn, vt, f

v, vn, vt, f = parse(OBJ)
print("=== Modeling Verification ===")
checks = [
    ("Verts", 50 <= len(v) <= 200, f"{len(v)} (50-200)"),
    ("Faces", 30 <= len(f) <= 150, f"{len(f)} (30-150)"),
    ("Triangles", all(len(re.findall(r'\d+/\d*/\d*', x))==3 for x in f), "all tri"),
    ("Normals", all(abs(math.sqrt(x*x+y*y+z*z)-1.0)<=0.01 for x,y,z in vn), f"{len(vn)} normalized"),
    ("UV range", all(0<=u<=1 and 0<=vc<=1 for u,vc in vt), f"{len(vt)} in [0,1]"),
    ("Indices", all(all(1<=int(m.group(1))<=len(v) for m in re.finditer(r'(\d+)/(\d*)/(\d*)', x)) for x in f), "no bad idx"),
]
allok = True
for name, ok, msg in checks:
    allok = allok and ok
    print(f"  {'PASS' if ok else 'FAIL'} - {name}: {msg}")
print(f"\nOverall: {'ALL PASS' if allok else 'ISSUES'}")
