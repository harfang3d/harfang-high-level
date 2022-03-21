import HarfangHighLevel as hl
from math import *
import random

hl.Init(1024, 768)
hl.AddFpsCamera(0, 20, -50)
hl.SetCamSpeed(20)

# add light
hl.AddLinearLight(0.33, 1.02, 0, hl.Color(1, 0.9, 1), False)
hl.AddPointLight(30, 20, 25, hl.Color(0.36, 0.6, 0.89))


sphereRadius = 0.1

# create ground
hl.AddPhysicBox(0, -0.25, 0, size_x=10, size_y=0.5, size_z=10, mass=0)

# physic falling cube
fallingCube = hl.AddPhysicBox(0, 5, 0, mass=0.4)

# physic cube with push impulse
pushedCube = hl.AddPhysicBox(0, 1.5, 3, mass=0.4)

# physic cube on top of the previous cube
cubeOnTop = hl.AddPhysicBox(0, 3, 3, mass=0.4)

# kinematic cube
kinematicCubeAllerRetour = hl.AddPhysicBox(0, 1.5, 0, 0, is_kinematic=True)

kinematicCubeTestMoveAfterFreeze = hl.AddPhysicBox(0, 10, 0, 0, is_kinematic=True)

# rain of spheres
spheresRainTestMoveAfterFreeze = []
for i in range(16):
    spheresRainTestMoveAfterFreeze.append(hl.AddPhysicSphere(1 + random.randrange(-50, 50) * 0.01, 12, random.randrange(-50, 50) * 0.01, radius=sphereRadius, mass=0.4))


# aligned cube to try the raycast full hits
for i in range(6):
    # one on two are kinematic
    if i % 2:
        hl.AddPhysicBox(i * 1.5 - 3, 0.6, -3, mass=0.4, is_kinematic=True)
    else:
        hl.AddPhysicBox(i * 1.5 - 3, 0.6, -3, mass=0.4, is_kinematic=False)


# parents node
parentsNode = []
previousNode = parentNode = hl.AddPhysicBox(-3, 5, -3, 0, is_kinematic=True)
parentsNode.append(previousNode)
for i in range(5):
    if previousNode.IsValid():
        childNode = hl.AddPhysicBox(1.5, 0, 0, 0, is_kinematic=True)
        childNode.GetTransform().SetParent(previousNode)
        previousNode = childNode
        parentsNode.append(childNode)


# node with multiple collisions shape
# using directly harfang and not HHL
nodeMutipleShapes = hl.AddBox(3, 5, 3)
rb = hl.gVal.scene.CreateRigidBody()
rb.SetType(hl.RBT_Static)

# add sphere collision
mesh_col = hl.gVal.scene.CreateCollision()
mesh_col.SetType(hl.CT_Sphere)
mesh_col.SetMass(0)
mesh_col.SetRadius(0.5)
nodeMutipleShapes.SetCollision(0, mesh_col)

# add cube collision on the side
col1 = hl.gVal.scene.CreateCollision()
col1.SetType(hl.CT_Cube)
col1.SetMass(0)
col1.SetSize(hl.Vec3(1, 0.1, 1))
col1.SetLocalTransform(hl.TranslationMat4(hl.Vec3(-0.7, 0.45, 0)))
nodeMutipleShapes.SetCollision(1, col1)

# add cube collision on the side
col2 = hl.gVal.scene.CreateCollision()
col2.SetType(hl.CT_Cube)
col2.SetMass(0)
col2.SetSize(hl.Vec3(1, 0.1, 1))
col2.SetLocalTransform(hl.TranslationMat4(hl.Vec3(0.7, 0.45, 0)))
nodeMutipleShapes.SetCollision(2, col2)

nodeMutipleShapes.SetRigidBody(rb)
hl.gVal.scene.Update(0)  # NEED TO UPDATE THE SCENE TO HAVE THE WORLD MATRIX UPDATED TO INITIALIZE THE PHYSIC
hl.gVal.physics.NodeCreatePhysicsFromAssets(nodeMutipleShapes)


# rain of spheres
spheresRain = []
for i in range(16):
    spheresRain.append(hl.AddPhysicSphere(3 + random.randrange(-50, 50) * 0.01, 7, 3 + random.randrange(-50, 50) * 0.01, radius=sphereRadius, mass=0.4))


# create absorbant ground
rollingSpheres = []
for i in range(5):
    ground_absorb = hl.AddPhysicBox(12 + i * 2, -0.25, 0, size_x=1, size_y=0.5, size_z=20, mass=0, friction=i * 0.1, rolling_friction=i - 0.1)
    # create rolling sphere
    rollingSpheres.append(hl.AddPhysicSphere(12 + i * 2, 1, 9, radius=sphereRadius, mass=0.4))


# test restitution
ground_restitution = hl.AddPhysicBox(-17, -0.25, 0, size_x=10, size_y=0.5, size_z=20, mass=0, friction=0)
ground_restitution_border = hl.AddPhysicBox(-21, 1, 0, size_x=0.5, size_y=2, size_z=20, mass=0, friction=0, restitution=1)
restitutionSphere = hl.AddPhysicSphere(-13, 1, 9, radius=sphereRadius, mass=0.4, restitution=1)

# # lock axes
ground_lock_axes = hl.AddPhysicBox(20, -0.25, 20, size_x=2, size_y=0.5, size_z=2, mass=0)
ground_little_wall_lock_axes_right = hl.AddPhysicBox(21.25, -0.25, 20, 0, 0, -0.3, 0.5, 10, 0.5, 0)
ground_little_wall_lock_axes_left = hl.AddPhysicBox(18.75, -0.25, 20, 0, 0, 0.3, 0.5, 10, 0.5, 0)

sphereLockAxes = []
for i in range(32):
    sphereLockAxes.append(hl.AddPhysicSphere(20 + random.randrange(-50, 50) / 50, 7 + random.randrange(50), 20, radius=sphereRadius, mass=0.4))

# setup lock axes AFTER init physic
for sphereLockAxe in sphereLockAxes:
    hl.gVal.physics.NodeSetLinearFactor(sphereLockAxe, hl.Vec3(1, 1, 0))

# create chain
chainNodes = []
chainNodes.append(hl.AddPhysicSphere(0, 5, 10, radius=sphereRadius, mass=0))
for i in range(16):
    chainNodes.append(hl.AddPhysicSphere(i * 0.2, 5, 10, radius=sphereRadius, mass=0.4))

# setup constraint
for i in range(1, len(chainNodes)):
    hl.gVal.physics.NodeAddConstraint(chainNodes[i - 1], chainNodes[i], hl.Mat4.Identity, hl.TranslationMat4(hl.Vec3(0.2, 0, 0)))

# test trigger
triggerNode = hl.AddPhysicBox(0, 0.2, 0, is_trigger=True, mass=0)
hl.gVal.physics.NodeStartTrackingCollisionEvents(triggerNode, hl.CETM_EventAndContacts)

# disable deactivation
hl.gVal.physics.NodeSetDeactivation(kinematicCubeAllerRetour, True)
hl.gVal.physics.NodeSetDeactivation(kinematicCubeTestMoveAfterFreeze, True)
for n in parentsNode:
    hl.gVal.physics.NodeSetDeactivation(n, True)

while not hl.UpdateDraw():
    # launch a sphere (radius: 0.05, weight: .5kg) from the camera to the front
    if hl.KeyPressed(hl.K_Space):
        cam_matrix = hl.GetCameraMat4()
        node_sphere = hl.AddPhysicSphereM(cam_matrix, 0.05, 0.5)
        hl.NodeAddImpulse(node_sphere, hl.GetZ(cam_matrix) * 20.0)

    if hl.ImGuiBegin("Options"):
        change, hl.gVal.debug_physics = hl.ImGuiCheckbox("Activate Physic Debug", hl.gVal.debug_physics)
    hl.ImGuiEnd()

    c = hl.time_to_sec_f(hl.GetClock())
    length = 5
    p0 = hl.Vec3(sin(c) * length, 0.5, cos(c) * length)
    p1 = hl.Vec3(sin(c) * -length, 0.5, cos(c) * -length)
    hl.DrawCrossV(p0, hl.Color.White, 0.1)
    hl.DrawLineV(p0, p1)

    # first hit
    hit = hl.gVal.physics.RaycastFirstHit(hl.gVal.scene, p0, p1)
    if hit.node.IsValid():
        hl.DrawText2D("hit", 10, 10)
        hl.DrawCrossV(hit.P, hl.Color.Blue, 0.1)
    else:
        hl.DrawText2D("no hit", 10, 10)

    # move the kinematic
    hl.SetPosition(kinematicCubeAllerRetour, sin(c) * 10, 0.5, 0)
    hl.gVal.physics.NodeWake(kinematicCubeAllerRetour)

    # push the cube
    if hl.ReturnTrueEveryXSec(1, "SampleRaycast_pushedNode"):
        hl.NodeAddImpulse(pushedCube, hl.Vec3(0, 3, 0))

    # full raycast
    p3 = hl.Vec3(8, 0.5, -3)
    p4 = hl.Vec3(-8, 0.5, -3)
    hl.DrawCrossV(p3, hl.Color.White, 0.1)
    hl.DrawLineV(p3, p4)

    hits = hl.gVal.physics.RaycastAllHits(hl.gVal.scene, p3, p4)
    for h in hits:
        if h.node.IsValid():
            hl.DrawCrossV(h.P, hl.Color.Blue, 0.1)

    # reset falling cube
    if hl.KeyPressed(hl.K_R):
        hl.ResetWorldAndForce(fallingCube, 0, 5, 0)

    # move parent node
    hl.SetPosition(parentNode, cos(c) * 10 - 3, 5, -3)

    # first hit kinematic parent
    p5 = hl.Vec3(-3, 5, -6)
    p6 = hl.Vec3(-3, 5, -1)
    hl.DrawCrossV(p5, hl.Color.White, 0.1)
    hl.DrawLineV(p5, p6)
    hitParent = hl.gVal.physics.RaycastFirstHit(hl.gVal.scene, p5, p6)
    if hitParent.node.IsValid():
        hl.DrawCrossV(hitParent.P, hl.Color.Blue, 0.1)

    # reset rain sphere
    for sphereRain in spheresRain:
        if hl.GetT(sphereRain.GetTransform().GetWorld()).y < 2:
            hl.ResetWorldAndForce(sphereRain, 3 + random.randrange(-50, 50) * 0.01, 7, 3 + random.randrange(-50, 50) * 0.01)

    # press to move the kinematic
    if hl.KeyPressed(hl.K_T):
        hl.ResetWorldAndForce(kinematicCubeTestMoveAfterFreeze, random.randrange(1) + 1, 10, 0)

    for sphereRain in spheresRainTestMoveAfterFreeze:
        if hl.GetT(sphereRain.GetTransform().GetWorld()).y < 5:
            hl.ResetWorldAndForce(sphereRain, 1 + random.randrange(-50, 50) * 0.02, 12, random.randrange(-50, 50) * 0.01)

    # update rolling sphere
    if hl.KeyPressed(hl.K_G):
        count = 0
        for rollingSphere in rollingSpheres:
            hl.DrawText(f"Friction: {count*0.1:.2f}", 12 + count * 2, 2, 9)
            hl.ResetWorldAndForce(rollingSphere, 12 + count * 2, 1, 9)

            hl.NodeAddImpulse(rollingSphere, hl.Vec3(0, 0, -1))
            count += 1

    for i in range(len(rollingSpheres)):
        hl.DrawText(f"Friction: {i * 0.1:.2f}", 12 + i * 2, 2, 9, size=0.01)

    # restitution test
    if hl.KeyPressed(hl.K_F):
        hl.SetPosition(restitutionSphere, -13, 1, 9)
        hl.NodeAddImpulse(restitutionSphere, hl.Vec3(-1, 0, -1))

    # lock axes
    if hl.KeyPressed(hl.K_V):
        for i in range(len(sphereLockAxes)):
            hl.ResetWorldAndForce(sphereLockAxes[i], 20 + (random.randrange(-50, 50)) / 50, 7 + random.randrange(50), 20)

    # chain
    if hl.KeyPressed(hl.K_B):
        for i in range(len(chainNodes)):
            hl.ResetWorldAndForce(chainNodes[i], i * 0.2, 5, 10)

    # test trigger
    nodeContacts = hl.gVal.physics.NodeCollideWorld(triggerNode, triggerNode.GetTransform().GetWorld(), 10)
    nodeInContact = hl.GetNodesInContact(hl.gVal.scene, triggerNode, nodeContacts)
    i = 0
    for n in nodeInContact:
        hl.DrawText(f"Contact: {n.GetName()}", 0, 0.5 + i * 0.5, 0, size=0.01)
        i += 1

        contacts = hl.GetNodePairContacts(triggerNode, n, nodeContacts)
        for contact in contacts:
            hl.DrawCrossV(contact.P, hl.Color.Red)

hl.Uninit()
