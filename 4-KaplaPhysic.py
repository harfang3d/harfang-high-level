import HarfangHighLevel as hl
from math import *

hl.Init(1024, 768)
hl.AddFpsCamera(0, 20, -50)
hl.AddPhysicBox(0, -0.25, 0, size_x=50, size_y=0.1, size_z=50, mass=0)

# hl.gVal.debug_physics = True


def add_kapla_tower(width, height, length, radius, level_count, x, y, z):
    # Create a Kapla tower, return a list of created nodes
    level_y = y + height / 2

    nodes = []

    for i in range(level_count // 2):

        def fill_ring(r, ring_y, size, r_adjust, y_off):
            step = asin((size) / 2 / (r - r_adjust)) * 2
            box_count = (2 * pi) // step
            error = 2 * pi - step * box_count
            step += error / box_count  # distribute error

            a = 0
            while a < (2 * pi - error):
                node_kapla = hl.AddPhysicBox(cos(a) * r + x, ring_y, sin(a) * r + z, 0, -a + y_off, 0, width, height, length, 0.4)
                nodes.append(node_kapla)
                a += step

        fill_ring(radius - length / 2, level_y, width, length / 2, pi / 2)
        level_y += height
        fill_ring(radius - length + width / 2, level_y, length, width / 2, 0)
        fill_ring(radius - width / 2, level_y, length, width / 2, 0)
        level_y += height

    return nodes


# create the kapla tower
add_kapla_tower(0.5, 2, 2, 6, 12, -12, 0, 0)
add_kapla_tower(0.5, 2, 2, 6, 12, 12, 0, 0)


while not hl.UpdateDraw():
    # launch a sphere (radius: 0.05, weight: .5kg) from the camera to the front
    if hl.KeyPressed(hl.K_Space):
        cam_matrix = hl.GetCameraMat4()
        node_sphere = hl.AddPhysicSphereM(cam_matrix, 0.05, 0.5)
        hl.NodeAddImpulse(node_sphere, hl.GetZ(cam_matrix) * 20.0)

hl.Uninit()
