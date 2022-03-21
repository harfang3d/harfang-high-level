import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512)

# Simple scene (camera, light, box model)
hl.AddFpsCamera(0, 2, -2, pi/4)
hl.AddPointLight(1, 2, 1)
hl.AddBox(0, 0, 0, 0, pi/4, 0)

while not hl.UpdateDraw():
    pass

hl.Uninit()
