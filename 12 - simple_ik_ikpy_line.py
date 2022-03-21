import numpy as np

# IKPy imports
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from ikpy.utils import geometry

import HarfangHighLevel as hl
from math import sin, cos, pi
import time

# init chain
arm_chain = Chain(
    name="arm",
    links=[
        URDFLink(name="shoulder", origin_translation=[1, 0, 0], origin_orientation=[0, 0, 0], rotation=[0, 0, 1],),
        URDFLink(name="elbow", origin_translation=[1, 0, 0], origin_orientation=[0, 0, 0], rotation=[0, 0, 1],),
        URDFLink(name="wrist", origin_translation=[1, 0, 0], origin_orientation=[0, 0, 0], rotation=[0, 0, 1],),
    ],
)

# joints arm
arm_joint = [0] * len(arm_chain.links)

# init window
hl.Init(1024, 1024)

# Simple scene (camera, light, box model)
hl.AddFpsCamera(0, 2, -2, pi / 4)
hl.AddPointLight(1, 2, 1)

vec_target = hl.Vec3(0.2, 0.3, -0.35)
start_chain_world_pos = hl.Vec3(0, 0, 0)


while not hl.UpdateDraw():

    if hl.ImGuiBegin("Target"):
        vec_target = hl.Vec3(cos(time.time()) * 0.5, 0.5 + sin(time.time()) * 0.2, 0)
        change, vec_target = hl.ImGuiSliderVec3("Target right hand", vec_target, -1, 1.0)
    hl.ImGuiEnd()

    # ik
    new_target = vec_target - start_chain_world_pos

    # Objectives 1
    target = [new_target.x, new_target.y, new_target.z]

    frame_target = np.eye(4)
    frame_target[:3, 3] = target

    arm_joint = arm_chain.inverse_kinematics_frame(frame_target, initial_position=arm_joint, max_iter=4)

    # draw target
    hl.DrawCrossV(vec_target, hl.Color.Purple)

    # draw lines from the arm
    transformation_matrixes = arm_chain.forward_kinematics(arm_joint, full_kinematics=True)

    # Get the pos and the orientation from the tranformation matrix
    prev_pos = None
    for (index, link) in enumerate(arm_chain.links):
        (pos, orientation) = geometry.from_transformation_matrix(transformation_matrixes[index])

        p = start_chain_world_pos + hl.Vec3(pos[0], pos[1], pos[2])

        # Plot the chain
        # draw joint
        hl.DrawCrossV(p, hl.Color.Red, 0.05)

        if prev_pos is not None:
            hl.DrawLineV(prev_pos, p)
        prev_pos = p


hl.Uninit()

