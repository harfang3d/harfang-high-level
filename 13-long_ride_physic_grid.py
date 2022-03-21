import HarfangHighLevel as hl
from math import *
from random import random, randrange

hl.Init(1024, 768)
# hl.gVal.debug_physics = True
waitFewFrameBeforeTeleportAgain = 0

camFollowSphere = True
if not camFollowSphere:
    hl.AddFpsCamera(0, 50, -2, pi / 2)

gridSize = hl.Vec2(50, 50)
gridWorld = []
lengthGrid = 5
for x in range(-lengthGrid, lengthGrid):
    gridWorld_x = []
    for y in range(-lengthGrid, lengthGrid):
        nodes = [
            {
                "n": hl.AddPhysicBox(x * gridSize.x, -0.25, y * gridSize.y, size_x=gridSize.x, size_y=0.1, size_z=gridSize.y, mass=0, color=hl.Color(random(), random(), random())),
                "o": hl.Vec3(x * gridSize.x, -0.25, y * gridSize.y),
            }
        ]

        # randomly add an object or not
        rand = randrange(0, 5)
        item_added = None
        offset_pos = hl.Vec3(0, 0, 0)
        if rand == 0:
            # drone
            item_added = hl.Add3DFile("3d_models/buster_drone/scene.gltf")
            # drone are too big, reduce the scale, push it a bit on the front
            hl.SetScale(item_added, 0.05, 0.05, 0.05)
            offset_pos.y = 5
        elif rand == 1:
            item_added = hl.Add3DFile("3d_models/pony-cartoon/Pony_cartoon.obj")
            hl.SetScale(item_added, 0.01, 0.01, 0.01)
        elif rand == 2:
            item_added = hl.Add3DFile("3d_models/tonneau/scene.gltf")
            hl.SetScale(item_added, 3, 3, 3)

        elif rand == 3:
            # load lod
            item_added = hl.LOD_Manager.CreateNodeWithLOD(
                "test",
                [
                    {"path": "3d_models/lod/lod0.glb", "distance": 1},
                    {"path": "3d_models/lod/lod1.glb", "distance": 2},
                    {"path": "3d_models/lod/lod2.glb", "distance": 3},
                    {"path": "3d_models/lod/lod3.glb", "distance": 4},
                    {"path": "3d_models/lod/lod4.glb"},
                ],
            )
            hl.SetScale(item_added, 3, 3, 3)

        if item_added is not None:
            p = hl.Vec3(x * gridSize.x + randrange(-gridSize.x // 2, gridSize.x // 2), 0, y * gridSize.y + randrange(-gridSize.y // 2, gridSize.y // 2)) + offset_pos
            hl.SetPositionV(item_added, p)
            nodes.append({"n": item_added, "o": p})

        # append all nodes to the gridWorld
        gridWorld_x.append(nodes)
    gridWorld.append(gridWorld_x)

massSphere = 10
nodeSphere = hl.AddPhysicSphere(0, 2, 0, radius=0.5, mass=massSphere)

worldSimulatedCenter = hl.Vec3(0, 0, 0)


def TeleportDynamicPhysicObject(n, shift):
    # respawn the physic object to the other side
    hl.SetPositionV(n, pos + shift)


# if out of grid, respawn on the other side
def Teleport(pos):
    global worldSimulatedCenter, waitFewFrameBeforeTeleportAgain
    objectHasBeenTeleportShift = None

    if pos.x > gridSize.x // 2 * 1.01:
        objectHasBeenTeleportShift = hl.Vec3(-gridSize.x, 0, 0)
    elif pos.z > gridSize.y // 2 * 1.01:
        objectHasBeenTeleportShift = hl.Vec3(0, 0, -gridSize.y)
    elif pos.x < -gridSize.x // 2 * 1.01:
        objectHasBeenTeleportShift = hl.Vec3(gridSize.x, 0, 0)
    elif pos.z < -gridSize.y // 2 * 1.01:
        objectHasBeenTeleportShift = hl.Vec3(0, 0, gridSize.y)

    if objectHasBeenTeleportShift is not None and waitFewFrameBeforeTeleportAgain < 0:
        waitFewFrameBeforeTeleportAgain = 5

        TeleportDynamicPhysicObject(nodeSphere, objectHasBeenTeleportShift)

        # update world center
        worldSimulatedCenter += objectHasBeenTeleportShift
        pos += objectHasBeenTeleportShift

        # slide the grid
        for x in gridWorld:
            for y in x:
                for n in y:
                    hl.SetPositionV(n["n"], n["o"] + worldSimulatedCenter)
    else:
        waitFewFrameBeforeTeleportAgain -= 1

    return pos


while not hl.UpdateDraw():
    # compute the force to stay up in the air
    pos = hl.GetT(nodeSphere.GetTransform().GetWorld())

    # if out of grid, respawn on the other side
    pos = Teleport(pos)

    if camFollowSphere:
        m = hl.gVal.camera.GetTransform().GetWorld()
        cam_rot = hl.GetR(m)
        cam_rot.y += hl.gVal.mouse.DtX() * 0.05

        z_axis = hl.GetZ(hl.RotationMat3(cam_rot))
        cam_pos = pos - z_axis * 10 + hl.Vec3(0, 2, 0)

        hl.gVal.camera.GetTransform().SetWorld(hl.TransformationMat4(cam_pos, cam_rot))

    # update force
    # little force to push forward
    linear_vel = hl.gVal.physics.NodeGetLinearVelocity(nodeSphere)
    vel_max = 10

    if camFollowSphere:
        cam_rot = hl.gVal.camera.GetTransform().GetRot()
        z_axis = hl.GetZ(hl.RotationMat3(hl.Vec3(0, cam_rot.y, 0)))
    else:
        z_axis = hl.Vec3(-1, 0, 0)

    F = z_axis * (50 * massSphere * (abs(vel_max - hl.Len(linear_vel)) / vel_max))
    hl.NodeAddForce(nodeSphere, F)
    hl.DrawLineV(pos, pos + F)

    # draw current world position
    hl.DrawText2D(f"Reel: {pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}", 512, 40, text_centered=True)
    hl.DrawText2D(f"World: {pos.x+worldSimulatedCenter.x:.2f}, {pos.y+worldSimulatedCenter.y:.2f}, {pos.z+worldSimulatedCenter.z:.2f}", 512, 20, text_centered=True)

hl.Uninit()
