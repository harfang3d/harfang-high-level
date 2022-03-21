import HarfangHighLevel as hl


class LOD_node:
    def __init__(self):
        self.LODs = []
        self.name = ""
        self.current_lod = 0
        self.actif = False

    def GetNode(self) -> hl.Node:
        return self.LODs[self.current_lod]["n"]


LOD_nodes = []

# lod_def = [{"path":"lod0.geo", "distance": 20},
# 			 {"path":"lod1.geo", "distance": 50},
# 			 {"path":"imposter.geo"}])
def CreateNodeWithLOD(name: str, lod_def, make_physics_object: bool = False, physic_type=hl.RBT_Static, collision_type=hl.CT_Mesh) -> LOD_node:
    node = LOD_node()
    node.name = name
    # share the same transform
    trs = hl.gVal.scene.CreateTransform(hl.Vec3(0, 0, 0), hl.Vec3(0, 0, 0))

    for id, lod in enumerate(lod_def):
        n = hl.Add3DFile(lod["path"], make_physics_object=make_physics_object, physic_type=physic_type, collision_type=collision_type)
        n.SetTransform(trs)
        if id != 0:
            n.Disable()
        l = {"n": n, "path": lod["path"]}
        if "distance" in lod:
            l["distance"] = lod["distance"]
            l["distance2"] = lod["distance"] ** 2
        node.LODs.append(l)

    LOD_nodes.append(node)

    return node


def SwitchLOD(node: LOD_node, lod_choice):
    if lod_choice < len(node.LODs):
        # get the world
        node.LODs[node.current_lod]["n"].Disable()
        node.current_lod = lod_choice
        n = node.LODs[node.current_lod]["n"]
        w = n.GetTransform().GetWorld()
        n.Enable()

        # don't update if the rigid body is in kinematic
        if n.HasRigidBody() and n.GetRigidBody().GetType() != hl.RBT_Kinematic:
            gVal.physics.NodeResetWorld(n, w)

    else:
        print(f"no lod for {node.name} with lod choice: {lod_choice}")


def UpdateLod(m: hl.Mat4):
    p = hl.GetT(m)
    # find the right lod
    for node in LOD_nodes:
        distance_to_node = hl.Len2(p - hl.GetT(node.LODs[node.current_lod]["n"].GetTransform().GetWorld()))
        # check if need to change lod
        # if last lod
        if node.current_lod > 0 and distance_to_node < node.LODs[node.current_lod - 1]["distance2"]:
            SwitchLOD(node, node.current_lod - 1)
        elif node.current_lod < len(node.LODs) - 1 and distance_to_node > node.LODs[node.current_lod]["distance2"]:
            SwitchLOD(node, node.current_lod + 1)
