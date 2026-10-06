"""Pasca-proses PNG RGBA hasil render shadow-catcher: potong alfa lantai tipis (<= T) agar tepi lantai tidak tampak sebagai kotak abu-abu pada lembar putih.
python post_alpha.py <T> <berkas.png> [...]   (alfa' = clip((alfa - T) / (255 - T)); piksel benda (alfa 255) tidak berubah)"""
import sys
import numpy as np
from PIL import Image

T = float(sys.argv[1])
for p in sys.argv[2:]:
    im = Image.open(p).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    al = a[..., 3]
    a2 = np.clip((al - T) / (255.0 - T), 0, 1) * 255.0
    out = a.copy(); out[..., 3] = a2
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGBA").save(p)
    print(p, "alfa maks lantai sebelum:", int(al[(al < 255)].max()) if (al < 255).any() else None)
