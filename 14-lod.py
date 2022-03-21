import HarfangHighLevel as hl
from math import pi

hl.Init(512, 512)

hl.AddFpsCamera(0, 2, -2, pi / 4)
hl.AddPointLight(1, 2, 1)

# load lod
LOD_node = hl.LOD_Manager.CreateNodeWithLOD(
    "test",
    [
        {"path": "3d_models/lod/lod0.glb", "distance": 1},
        {"path": "3d_models/lod/lod1.glb", "distance": 2},
        {"path": "3d_models/lod/lod2.glb", "distance": 3},
        {"path": "3d_models/lod/lod3.glb", "distance": 4},
        {"path": "3d_models/lod/lod4.glb"},
    ],
)

current_lod = 0
while not hl.UpdateDraw():

    if hl.ImGuiBegin("Test"):
        change, current_lod = hl.ImGuiSliderInt("lod", LOD_node.current_lod, 0, 4)

        # draw distance to the first lod
        p = hl.GetT(hl.gVal.camera.GetTransform().GetWorld())
        hl.ImGuiText(f"dist: {hl.Len2(p - hl.GetT(hl.LOD_Manager.LOD_nodes[0].LODs[hl.LOD_Manager.LOD_nodes[0].current_lod]['n'].GetTransform().GetWorld()))}")
    hl.ImGuiEnd()


hl.Uninit()
