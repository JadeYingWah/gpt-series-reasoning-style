from PIL import Image
import numpy as np

p = r"C:\Users\yutia\Desktop\弗糯糯炒饭\assets\funuonuo.png"
im = Image.open(p).convert("RGBA")
arr = np.array(im).astype(np.int16)
h, w = arr.shape[:2]
r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

# magenta-ish: high R, low G, high B
is_mag = (r > 140) & (b > 140) & (g < 120) & ((r - g) > 60) & ((b - g) > 40)
# also pure-ish magenta by hue
mag_score = (r.astype(int) + b.astype(int)) / 2 - g
is_mag = is_mag | ((mag_score > 70) & (r > 100) & (b > 100))

# soft alpha for edge magenta
score = mag_score.astype(float)
alpha = np.full((h, w), 255, dtype=np.float64)
# hard remove
alpha[is_mag] = 0
# soft fringe: strong magenta score but not classified hard
soft = (~is_mag) & (score > 45)
alpha[soft] = np.clip((1 - (score[soft] - 45) / 40) * 255, 0, 255)

arr[:, :, 3] = alpha.astype(np.uint8)
out = Image.fromarray(arr.astype(np.uint8), "RGBA")
out.save(p)
print("hard", int((alpha == 0).sum()), "soft", int(((alpha > 0) & (alpha < 255)).sum()))
print("alpha", out.getchannel("A").getextrema())
# sample center (should be character) and corner (should be 0)
a = np.array(out)
print("corner alpha", a[0, 0, 3], a[0, -1, 3], a[-1, 0, 3])
print("center alpha", a[h // 2, w // 2, 3])
print("apron area approx", a[int(h * 0.7), w // 2, 3])
