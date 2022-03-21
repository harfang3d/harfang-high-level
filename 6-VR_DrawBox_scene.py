import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512, True)

# Simple scene (camera, light, box model)
hl.AddFpsCamera(0, 2, -2, pi / 4)
hl.AddPointLight(1, 2, 1)
hl.AddBox(0, 0, 0, 0, pi / 4, 0)

# VR anchor
hl.SetVRGroundAnchor(0, 0, -2)  # set the vr anchor on the ground

# main loop
while not hl.UpdateDraw():
    # draw the controllers
    controllers_mat = hl.GetVRControllersMat()
    for m in controllers_mat:
        hl.DrawBoxM(m, hl.Vec3(0.05, 0.05, 0.05))

    hl.DrawBox(0, 1, 0)

hl.Uninit()
