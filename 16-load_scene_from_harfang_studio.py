import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512)
hl.AddFpsCamera(0, 2, -2, pi / 4)

# if not working, launch example 14-lod.py before
node = hl.LoadScene("lod_lod0_False_5_2_False/lod0.scn")

while not hl.UpdateDraw():
    pass

hl.Uninit()
