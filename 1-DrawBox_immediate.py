import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512)

# Simple scene (camera, light)
hl.AddFpsCamera(0, 2, -2, pi / 4)
hl.AddPointLight(1, 2, 1)

while not hl.UpdateDraw():
    hl.DrawBox(0, 0, 0)

hl.Uninit()
