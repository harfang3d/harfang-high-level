import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512)

hl.AddFpsCamera(-0.8, 3, -4, 0.6, -0.06, 0)
hl.AddPointLight(1, 2, 1)

# add 3d model to scene
avocado = hl.Add3DFile("3d_models/Avocado.fbx")
hl.SetScale(avocado, 10, 10, 10)

pony_cartoon = hl.Add3DFile("3d_models/pony-cartoon/Pony_cartoon.obj")
hl.SetPosition(pony_cartoon, 0, 2)
hl.SetScale(pony_cartoon, 0.001, 0.001, 0.001)

# barrel
barrel = hl.Add3DFile("3d_models/tonneau/scene.gltf")
hl.SetPosition(barrel, 2)

# drone
drone = hl.Add3DFile("3d_models/buster_drone/scene.gltf")
# drone are too big, reduce the scale, push it a bit on the front
hl.SetScale(drone, 0.01, 0.01, 0.01)
hl.SetPosition(drone, -2, 1, 0)

while not hl.UpdateDraw():
    pass

hl.Uninit()
