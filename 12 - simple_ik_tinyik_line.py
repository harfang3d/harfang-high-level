import tinyik
import numpy as np
from math import *
import time
import HarfangHighLevel as hl

# install
# pip install tinyik -U
# pip install open3d

hl.Init(1024, 1024)

hl.AddFpsCamera(1, 2, -2, pi / 4)
hl.AddPointLight(1, 2, 1)

start_chain_world_pos = hl.Vec3(0, 0, 0)
reachy_3D_right_arm_joint_node = []
actuators = [
    [0, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
    "z",
    [0.1, 0, 0],
]

arm = tinyik.Actuator(actuators, tinyik.ScipySmoothOptimizer(options={"maxiter": 1}))
# arm = tinyik.Actuator(actuators, tinyik.SteepestDescentOptimizer(maxiter=1))

target = hl.Vec3(0, 0, 0)
imgui_target_val = 0
imgui_origin_val = 0

while not hl.UpdateDraw():
    # only call once (because it's a getter function which call solver)
    arm.ee = [target.x - start_chain_world_pos.x, target.y - start_chain_world_pos.y, target.z - start_chain_world_pos.z]
    angles = arm.angles
    arm.components[0].coord = [start_chain_world_pos.x, start_chain_world_pos.y, start_chain_world_pos.z]

    # draw end of the arm
    hl.DrawCrossV(start_chain_world_pos + hl.Vec3(arm.ee[0], arm.ee[1], arm.ee[2]), hl.Color.Red)
    hl.DrawCrossV(start_chain_world_pos + hl.Vec3(target.x - start_chain_world_pos.x, target.y - start_chain_world_pos.y, target.z - start_chain_world_pos.z), hl.Color.Red)

    hl.ImGuiSetNextWindowPos(hl.Vec2(0, 50))
    if hl.ImGuiBegin("Target"):
        change, imgui_target_val = hl.ImGuiSliderFloat(f"angle", imgui_target_val, 0, 2 * pi)
        if change:
            target.x = sin(imgui_target_val) * 0.5
            target.y = cos(imgui_target_val) * 0.2
        change, imgui_origin_val = hl.ImGuiSliderFloat(f"origin", imgui_origin_val, 0, 2 * pi)
        if change:
            start_chain_world_pos.x = sin(imgui_origin_val) * 0.5
            start_chain_world_pos.y = cos(imgui_origin_val) * 0.2
    hl.ImGuiEnd()

    hl.ImGuiSetNextWindowPos(hl.Vec2(0, 150))
    if hl.ImGuiBegin("Angles", False, hl.ImGuiWindowFlags_AlwaysAutoResize):
        update_angle = False
        for i in range(len(angles)):
            change, angles[i] = hl.ImGuiSliderFloat(f"angle {i}", angles[i], -pi, pi)
            update_angle &= change
            if update_angle:
                arm.angles = angles

    hl.ImGuiEnd()

    # draw lines
    previous_m = None
    for id in range(0, len(arm.components), 2):

        def return_angle():
            if arm.components[id + 1].axis == "x":
                return hl.Vec3(angles[id // 2], 0, 0)
            if arm.components[id + 1].axis == "y":
                return hl.Vec3(0, angles[id // 2], 0)
            if arm.components[id + 1].axis == "z":
                return hl.Vec3(0, 0, angles[id // 2])

        p = hl.Vec3(arm.components[id].coord[0], arm.components[id].coord[1], arm.components[id].coord[2])

        if previous_m is None:
            previous_m = hl.TransformationMat4(p, return_angle())
        else:
            if id // 2 < len(angles):
                m = previous_m * hl.TransformationMat4(p, return_angle())
            else:
                m = previous_m * hl.TranslationMat4(p)
            hl.DrawLineV(start_chain_world_pos + hl.GetT(previous_m), start_chain_world_pos + hl.GetT(m))

            previous_m = m

        hl.DrawCrossV(start_chain_world_pos + hl.GetT(previous_m), size=0.1)


hl.Uninit()
