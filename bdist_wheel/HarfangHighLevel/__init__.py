#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2021-2021 Thomas Simonnet, Movida Production.

import importlib.util
import subprocess
import sys
import re
from tqdm import tqdm
from pyunpack import Archive
import glob
import json
import os
import shutil
import subprocess
import pathlib
import operator

from harfang import *
import harfang as hl

from HarfangHighLevel import LOD_Manager

from typing import Union, Any, List, Dict

current_folder_path = pathlib.Path(__file__).parent.resolve()


render_type = "VK"
# render_type = "DX11"


class GlobalVal:
    width: int = 128
    height: int = 128
    win: int = None
    pipeline: hl.ForwardPipelineAAA = None
    res: hl.PipelineResources = None
    render_data: hl.SceneForwardPipelineRenderData = hl.SceneForwardPipelineRenderData()
    pass_views: List[hl.SceneForwardPipelinePassViewId] = []

    # VR
    activate_VR: bool = False
    vr_controllers: Dict[str, hl.VRController] = {}
    ground_vr_mat: hl.Mat4 = hl.Mat4(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
    vr_left_fb: hl.OpenVREyeFrameBuffer = None
    vr_right_fb: hl.OpenVREyeFrameBuffer = None
    vr_state: hl.OpenVRState = None

    vtx_layouts: Dict[str, hl.VertexLayout] = {}
    materials: Dict[str, hl.Material] = {}
    models: Dict[str, hl.Model] = {}
    model_refs: Dict[str, hl.ModelRef] = {}
    shaders: Dict[str, Union[hl.PipelineProgram, hl.PipelineProgramRef]] = {}
    CacheTexturePathToUniformTargetTex: Dict[str, hl.UniformSetTexture] = {}

    dt: int = hl.TickClock()
    clocks: hl.SceneClocks = hl.SceneClocks()
    scene: hl.Scene = None
    camera: hl.Node = None
    update_fps_controller: bool = False
    cam_speed: float = 1.0
    physics = None
    debug_physics: bool = False

    models_3D: List[Dict[str, Any]] = []
    texts_3D: List[Dict[str, Any]] = []
    lines_3D: List[Dict[str, Any]] = []
    quads_3D: List[Dict[str, Any]] = []
    objects_2D: List[Dict[str, Any]] = []

    font: hl.Font = None
    mouse: hl.Mouse = hl.Mouse()
    keyboard: hl.Keyboard = hl.Keyboard()

    EventNameElapsedSec = {}


gVal = GlobalVal()
output_assets_path = os.path.join("Harfang", "resources")
output_assets_compiled_path = os.path.join("Harfang", "resources_compiled")

text_render_state = hl.ComputeRenderState(hl.BM_Alpha, hl.DT_Always, hl.FC_Disabled, False)


def Init(width: int, height: int, activate_vr: bool = False):
    # create local harfang folder
    # and copy the resources
    if not os.path.exists(os.path.join("Harfang", "resources")):
        os.makedirs(os.path.join("Harfang", "resources"))
        Archive(os.path.join(current_folder_path, "Harfang", "resources.7z")).extractall(os.path.join("Harfang", "resources"))

    # launch assetc to compile
    execute_assetc(os.path.join("Harfang", "resources"), os.path.join("Harfang", "resources_compiled"))

    # set debug build
    # hl.SetLogLevel(hl.LL_All)
    # hl.SetLogDetailed(True)

    # save the windows size
    gVal.width = width
    gVal.height = height

    # add the path to the assets compiled folder to be used internally by the engine to find the resources
    hl.AddAssetsFolder("Harfang/resources_compiled")

    # init input/window
    hl.InputInit()
    hl.WindowSystemInit()

    hl.AudioInit()

    # create window
    gVal.win = hl.NewWindow(gVal.width, gVal.height)
    if render_type == "DX11":
        hl.RenderInit(gVal.win, hl.RT_Direct3D11)
    if render_type == "VK":
        hl.RenderInit(gVal.win, hl.RT_Vulkan)
    hl.RenderReset(gVal.width, gVal.height, hl.RF_MSAA4X)

    # create pipeline/resource
    gVal.pipeline = hl.CreateForwardPipeline()
    gVal.res = hl.PipelineResources()

    # init imgui
    hl.ImGuiInit(13, hl.LoadProgramFromAssets("core/shader/imgui"), hl.LoadProgramFromAssets("core/shader/imgui_image"))

    # create VR if asked
    if activate_vr:
        if not hl.OpenVRInit():
            hl.Error("Can't open OpenVR")
        else:
            gVal.vr_left_fb = hl.OpenVRCreateEyeFrameBuffer(hl.OVRAA_MSAA4x)
            gVal.vr_right_fb = hl.OpenVRCreateEyeFrameBuffer(hl.OVRAA_MSAA4x)

            gVal.activate_VR = activate_vr

    # create scene
    gVal.scene = hl.Scene()

    # create scene camera
    gVal.camera = hl.CreateCamera(gVal.scene, hl.TransformationMat4(hl.Vec3(0, 1000, 0), hl.Vec3(0, 0, 0)), 0.1, 10000,)
    gVal.scene.SetCurrentCamera(gVal.camera)

    # create physic
    gVal.physics = hl.SceneBullet3Physics(4)
    gVal.physics.SceneCreatePhysicsFromAssets(gVal.scene)

    # create vertex layout
    gVal.vtx_layouts["PosFloatNormUInt8"] = hl.VertexLayoutPosFloatNormUInt8()
    gVal.vtx_layouts["PosFloatColorUInt8"] = hl.VertexLayoutPosFloatColorUInt8()

    vs_pos_tex0_decl = hl.VertexLayout()
    vs_pos_tex0_decl.Begin()
    vs_pos_tex0_decl.Add(hl.A_Position, 3, hl.AT_Float)
    vs_pos_tex0_decl.Add(hl.A_TexCoord0, 3, hl.AT_Float)
    vs_pos_tex0_decl.End()
    gVal.vtx_layouts["PosFloatTex0Float"] = vs_pos_tex0_decl

    # create box
    gVal.models["box"] = hl.CreateCubeModel(gVal.vtx_layouts["PosFloatNormUInt8"], 1, 1, 1)
    gVal.model_refs["box"] = gVal.res.AddModel("box", gVal.models["box"])
    gVal.models["plane"] = hl.CreatePlaneModel(gVal.vtx_layouts["PosFloatNormUInt8"], 1, 1, 2, 2)
    gVal.model_refs["plane"] = gVal.res.AddModel("plane", gVal.models["plane"])

    # create shaders
    gVal.shaders["pbr"] = hl.LoadPipelineProgramRefFromAssets("core/shader/pbr.hps", gVal.res, hl.GetForwardPipelineInfo())
    gVal.shaders["mdl_no_pipeline"] = hl.LoadProgramFromAssets("core/shader/mdl")
    gVal.shaders["pos_rgb"] = hl.LoadProgramFromAssets("core/shader/pos_rgb")
    gVal.shaders["font"] = hl.LoadProgramFromAssets("core/shader/font")
    gVal.shaders["tex0"] = hl.LoadProgramFromAssets("core/shader/texture")
    gVal.shaders["color"] = hl.LoadProgramFromAssets("core/shader/color")

    # create default grey material
    gVal.materials["0.5_0.5_0.5"] = hl.CreateMaterial(gVal.shaders["pbr"], "uBaseOpacityColor", hl.Vec4(0.5, 0.5, 0.5), "uOcclusionRoughnessMetalnessColor", hl.Vec4(1, 1, 1),)

    # add map for pbr shader
    t, info = hl.LoadTextureFromAssets("core/pbr/probe.hdr.irradiance", 0)
    gVal.scene.environment.irradiance_map = gVal.res.AddTexture("core/pbr/probe.hdr.irradiance", t)
    t, info = hl.LoadTextureFromAssets("core/pbr/probe.hdr.radiance", 0)
    gVal.scene.environment.radiance_map = gVal.res.AddTexture("core/pbr/probe.hdr.radiance", t)
    t, info = hl.LoadTextureFromAssets("core/pbr/brdf.dds", 0)
    gVal.scene.environment.brdf_map = gVal.res.AddTexture("core/pbr/brdf.dds", t)

    # load font
    gVal.font = hl.LoadFontFromAssets(
        "NotoSans-Regular.ttf",
        36,
        1024,
        1,
        "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ",
    )

    # begin frame for imgui
    hl.ImGuiBeginFrame(
        gVal.width, gVal.height, gVal.dt, gVal.mouse.GetState(), gVal.keyboard.GetState(),
    )


def execute_assetc(input_path: str, output_path: str):
    # launch assetc to compile the newly added
    cmd = f'"{current_folder_path}\\Harfang\\_bin\\assetc.exe" -api {render_type} -quiet -progress -t "{current_folder_path}\\Harfang\\_bin\\toolchains\\host-windows-x64-target-windows-x64" "{input_path}" "{output_path}"'

    def execute_com(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return iter(p.stdout.readline, b"")

    t = tqdm(total=100)
    percent_prec = 0
    for line in execute_com(cmd):
        txt = str(line)
        if "Progress" in txt:
            percent = int(re.findall("\d*%", txt)[0].split("%")[0])
            t.update(percent - percent_prec)
            percent_prec = percent


###############################################################################
# ADD
###############################################################################


def getColoredMaterial(color: hl.Color):
    """Creates a material using the chosen color. Returns *harfang.Material* object. Material is cached, meaning that if you create 2 material objects of the same color, modifying one of them will modify the other one as well."""
    name = f"{color.r:.2f}_{color.g:.2f}_{color.b:.2f}"
    if name not in gVal.materials:
        gVal.materials[name] = hl.CreateMaterial(gVal.shaders["pbr"], "uBaseOpacityColor", hl.Vec4(color.r, color.g, color.b), "uOcclusionRoughnessMetalnessColor", hl.Vec4(1, 1, 1),)
    return gVal.materials[name]


def AddFpsCamera(
    x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0,
):
    """Creates a fps controller state (uses scene main camera)."""
    AddFpsCameraV(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z))


def AddFpsCameraV(p: hl.Vec3, r: hl.Vec3):
    gVal.camera.GetTransform().SetPos(p)
    gVal.camera.GetTransform().SetRot(r)
    gVal.update_fps_controller = True


def AddPointLight(x: float, y: float, z: float, color: hl.Color = hl.Color.White, shadow: bool = True) -> hl.Node:
    """Initialize a PointLight Node in the scene. Returns *harfang.Node* object."""
    return hl.CreatePointLight(gVal.scene, hl.TranslationMat4(hl.Vec3(x, y, z)), 0, color, hl.Color.White, 0, hl.LST_Map if shadow else hl.LST_None,)


def AddSpotLight(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, color: hl.Color = hl.Color.White, shadow: bool = True,) -> hl.Node:
    """Initialize a SpotLight Node in the scene. Returns *harfang.Node* object."""
    return hl.CreateSpotLight(gVal.scene, hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), 0, 5, 30, color, hl.Color.White, 0, hl.LST_Map if shadow else hl.LST_None,)


def AddLinearLight(angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, color: hl.Color = hl.Color.White, shadow: bool = True,) -> hl.Node:
    """Initialize a LinearLight Node in the scene. Returns *harfang.Node* object."""
    return hl.CreateLinearLight(gVal.scene, hl.TransformationMat4(hl.Vec3(0, 0, 0), hl.Vec3(angle_x, angle_y, angle_z)), color, hl.Color.White, 0, hl.LST_Map if shadow else hl.LST_None,)


def AddBox(
    x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, size_x: float = 1, size_y: float = 1, size_z: float = 1, color: hl.Color = hl.Color.White,
) -> hl.Node:
    """Initialize a 3d box node in the scene. Returns *harfang.Node* object."""
    return AddBoxM(hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), size_x, size_y, size_z, color,)


def AddBoxM(m: hl.Mat4, size_x: float = 1, size_y: float = 1, size_z: float = 1, color: hl.Color = hl.Color.White,) -> hl.Node:
    model = hl.CreateCubeModel(gVal.vtx_layouts["PosFloatNormUInt8"], size_x, size_y, size_z)
    pos = hl.GetT(m)
    rot = hl.GetR(m)
    model_ref = gVal.res.AddModel(f"box_{pos.x}_{pos.y}_{pos.z}_{rot.x}_{rot.y}_{rot.z}_{size_x}_{size_y}_{size_z}", model,)
    return hl.CreateObject(gVal.scene, m, model_ref, [getColoredMaterial(color)])


def AddPhysicBox(
    x: float,
    y: float,
    z: float,
    angle_x: float = 0,
    angle_y: float = 0,
    angle_z: float = 0,
    size_x: float = 1,
    size_y: float = 1,
    size_z: float = 1,
    mass: float = 0,
    friction=0.5,
    rolling_friction=0.0,
    restitution=0.0,
    is_kinematic: bool = False,
    is_trigger: bool = False,
    color: hl.Color = hl.Color.White,
) -> hl.Node:
    """Initialize a 3d physic box node in the scene. Returns *harfang.Node* object."""
    return AddPhysicBoxM(
        hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), size_x, size_y, size_z, mass, friction, rolling_friction, restitution, is_kinematic, is_trigger, color,
    )


def AddPhysicBoxM(
    m: hl.Mat4,
    size_x: float = 1,
    size_y: float = 1,
    size_z: float = 1,
    mass: float = 0,
    friction=0.5,
    rolling_friction=0.0,
    restitution=0.0,
    is_kinematic: bool = False,
    is_trigger: bool = False,
    color: hl.Color = hl.Color.White,
) -> hl.Node:
    node = AddBoxM(m, size_x, size_y, size_z, color)

    # create collision mesh
    mesh_col = gVal.scene.CreateCollision()
    mesh_col.SetType(hl.CT_Cube)
    mesh_col.SetMass(mass)
    mesh_col.SetSize(hl.Vec3(size_x, size_y, size_z))

    node.SetCollision(0, mesh_col)

    # create rigid body
    rb = gVal.scene.CreateRigidBody()

    if is_trigger:
        rb.SetType(hl.RBT_Trigger)
    elif is_kinematic:
        rb.SetType(hl.RBT_Kinematic)
    elif mass <= 0:
        rb.SetType(hl.RBT_Static)

    rb.SetFriction(friction)
    rb.SetRollingFriction(rolling_friction)
    rb.SetRestitution(restitution)

    node.SetRigidBody(rb)

    gVal.scene.Update(0)  # NEED TO UPDATE THE SCENE TO HAVE THE WORLD MATRIX UPDATED TO INITIALIZE THE PHYSIC
    gVal.physics.NodeCreatePhysicsFromAssets(node)
    return node


def AddSphere(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, radius: float = 1, color: hl.Color = hl.Color.White,) -> hl.Node:
    """Initialize a 3d sphere node in the scene. Returns *harfang.Node* object."""
    return AddSphereM(hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), radius, color,)


def AddSphereM(m: hl.Mat4, radius: float = 1, color: hl.Color = hl.Color.White) -> hl.Node:
    model = hl.CreateSphereModel(gVal.vtx_layouts["PosFloatNormUInt8"], radius, 16, 16)
    pos = hl.GetT(m)
    rot = hl.GetR(m)
    model_ref = gVal.res.AddModel(f"sphere_{pos.x}_{pos.y}_{pos.z}_{rot.x}_{rot.y}_{rot.z}_{radius}", model)
    return hl.CreateObject(gVal.scene, m, model_ref, [getColoredMaterial(color)])


def AddPhysicSphere(
    x: float,
    y: float,
    z: float,
    angle_x: float = 0,
    angle_y: float = 0,
    angle_z: float = 0,
    radius: float = 1,
    mass: float = 0,
    friction=0.5,
    rolling_friction=0.0,
    restitution=0.0,
    is_kinematic: bool = False,
    is_trigger: bool = False,
    color: hl.Color = hl.Color.White,
) -> hl.Node:
    """Initialize a 3d physic sphere node in the scene. Returns *harfang.Node* object."""
    return AddPhysicSphereM(hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), radius, mass, friction, rolling_friction, restitution, is_kinematic, is_trigger, color,)


def AddPhysicSphereM(
    m: hl.Mat4, radius: float = 1, mass: float = 0, friction=0.5, rolling_friction=0.0, restitution=0.0, is_kinematic: bool = False, is_trigger: bool = False, color: hl.Color = hl.Color.White,
) -> hl.Node:
    node = AddSphereM(m, radius, color)

    # create collision mesh
    mesh_col = gVal.scene.CreateCollision()
    mesh_col.SetType(hl.CT_Sphere)
    mesh_col.SetMass(mass)
    mesh_col.SetRadius(radius)

    node.SetCollision(0, mesh_col)

    # create rigid body
    rb = gVal.scene.CreateRigidBody()
    gVal.scene.Update(0)

    if is_trigger:
        rb.SetType(hl.RBT_Trigger)
    elif is_kinematic:
        rb.SetType(hl.RBT_Kinematic)
    elif mass <= 0:
        rb.SetType(hl.RBT_Static)

    rb.SetFriction(friction)
    rb.SetRollingFriction(rolling_friction)
    rb.SetRestitution(restitution)

    node.SetRigidBody(rb)

    gVal.scene.Update(0)  # NEED TO UPDATE THE SCENE TO HAVE THE WORLD MATRIX UPDATED TO INITIALIZE THE PHYSIC
    gVal.physics.NodeCreatePhysicsFromAssets(node)

    return node


def AddPlane(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, size_x: float = 1, size_y: float = 1, color: hl.Color = hl.Color.White,) -> hl.Node:
    """Initialize a 3d plane node in the scene. Returns *harfang.Node* object."""
    AddPlaneM(
        hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), size_x, size_y, color,
    )


def AddPlaneM(m: hl.Mat4, size_x: float = 1, size_y: float = 1, color: hl.Color = hl.Color.White) -> hl.Node:
    model = hl.CreatePlaneModel(gVal.vtx_layouts["PosFloatNormUInt8"], size_x, size_y, 2, 2)
    model_ref = gVal.res.AddModel(f"plane_{x}_{y}_{z}_{angle_x}_{angle_y}_{angle_z}_{size_x}_{size_y}", model)
    return hl.CreateObject(gVal.scene, m, model_ref, [getColoredMaterial(color)])


def AddCylinder(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, radius: float = 1, height: float = 2, color: hl.Color = hl.Color.White,) -> hl.Node:
    """Iinitialize a 3d cylinder node in the scene. Returns *harfang.Node* object."""
    model = hl.CreateCylinderModel(gVal.vtx_layouts["PosFloatNormUInt8"], radius, height, 16)
    model_ref = gVal.res.AddModel(f"cylinder_{x}_{y}_{z}_{angle_x}_{angle_y}_{angle_z}_{radius}_{height}", model)
    return hl.CreateObject(gVal.scene, hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), model_ref, [getColoredMaterial(color)],)


def AddCone(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, radius: float = 1, height: float = 2, color: hl.Color = hl.Color.White,) -> hl.Node:
    """Initialize a 3d cone node in the scene. Returns *harfang.Node* object."""
    model = hl.CreateConeModel(gVal.vtx_layouts["PosFloatNormUInt8"], radius, height, 16, 16)
    model_ref = gVal.res.AddModel(f"cone_{x}_{y}_{z}_{angle_x}_{angle_y}_{angle_z}_{radius}_{height}", model)
    return hl.CreateObject(gVal.scene, hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), model_ref, [getColoredMaterial(color)],)


def AddCapsule(x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, radius: float = 1, height: float = 2, color: hl.Color = hl.Color.White,) -> hl.Node:
    """Initialize a 3d capsule node in the scene. Returns *harfang.Node* object."""
    model = hl.CreateCapsuleModel(gVal.vtx_layouts["PosFloatNormUInt8"], radius, height, 16, 16)
    model_ref = gVal.res.AddModel(f"capsule_{x}_{y}_{z}_{angle_x}_{angle_y}_{angle_z}_{radius}_{height}", model)
    return hl.CreateObject(gVal.scene, hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), model_ref, [getColoredMaterial(color)],)


def LoadScene(scn_path: str):
    """Creates a new instance of a 3d object such as a scene or an asset. Returns *harfang.Node*, *bool* object."""
    return hl.CreateInstanceFromAssets(gVal.scene, hl.Mat4.Identity, scn_path, gVal.res, hl.GetForwardPipelineInfo())[0]


###############################################################################
# IMPORT
###############################################################################


def Add3DFile(
    file_path: str,
    override: bool = False,
    make_physics_object: bool = False,
    physic_type=hl.RBT_Static,
    collision_type=hl.CT_Mesh,
    physic_mass=0,
    friction=0.5,
    rolling_friction=0,
    make_pathfinding: bool = False,
) -> hl.Node:
    """Creates a new instance of a 3d object by giving the path to the .fbx or .gltf model. Returns *harfang.Node* object."""
    # frist check if 3D file path exists
    if not os.path.exists(file_path):
        print("The path " + file_path + " does not exist")
        return None

    scene_file_name = f"{os.path.split(os.path.dirname(file_path))[-1]}_{os.path.splitext(os.path.basename(file_path))[0]}_{make_physics_object}_{collision_type}_{physic_type}_{make_pathfinding}"
    scene_folder_name = scene_file_name

    output_import_path = os.path.join(output_assets_path, scene_file_name)

    # check if the folder not existing or override is set
    if (os.path.exists(output_import_path) and override) or (not os.path.exists(output_import_path)):
        if os.path.exists(output_import_path):
            shutil.rmtree(output_import_path)
        os.makedirs(output_import_path)

        # import
        # choose the right importer
        ext = os.path.splitext(file_path)
        if ext == ".gltf" or ext == ".glb":
            command_line = f'"{current_folder_path}\\Harfang\\_bin\\gltf_importer.exe" "{file_path}" -fix-geometry-orientation -o "{output_import_path}/" -base-resource-path "{output_assets_path}" -material-policy overwrite -geometry-policy overwrite -texture-policy overwrite -scene-policy overwrite'
        elif ext == ".fbx":
            command_line = f'"{current_folder_path}\\Harfang\\_bin\\fbx_importer.exe" "{file_path}" -profile pbr_physical -fix-geometry-orientation -o "{output_import_path}/" -base-resource-path "{output_assets_path}" -material-policy overwrite -geometry-policy overwrite -texture-policy overwrite -scene-policy overwrite'
        else:
            command_line = f'"{current_folder_path}\\Harfang\\_bin\\assimp_converter.exe" "{file_path}" -profile pbr_physical -o "{output_import_path}/" -base-resource-path "{output_assets_path}" -material-policy overwrite -geometry-policy overwrite -texture-policy overwrite -scene-policy overwrite'

        p = subprocess.Popen(command_line)
        stream_data = p.communicate()[0]
        print(stream_data)

        # add a meta with physics for almost all geo
        if make_physics_object:
            for file in glob.iglob(os.path.join(output_import_path, "*.geo")):
                rel_path = os.path.relpath(file, output_assets_path).replace("\\", "/")
                meta_text = '{"collision":{"input":[{"geometry":"' + rel_path + '","matrix":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],"type":'
                if collision_type == hl.CT_Mesh:
                    meta_text += '"triangle"'
                elif collision_type == hl.CT_MeshConvex:
                    meta_text += '"convex"'

                meta_text += '}],"type":"tree"}}'
                with open(file + ".physics", "w") as outfile:
                    outfile.write(meta_text)

        # add a meta with pathfinding for almost all geo
        if make_pathfinding:
            meta_text = '{"profiles": {"default": {"cook-pathfinding": true, "pathfinding-radius": 0.6, "pathfinding-height": 2.0, "pathfinding-slope": 0.78}}}'
            for file in glob.iglob(os.path.join(output_import_path, "pathfinding*.geo")):
                with open(file + ".meta", "w") as outfile:
                    outfile.write(meta_text)

        # launch assetc to compile
        execute_assetc(output_assets_path, output_assets_compiled_path)

    # find the scene
    scenes = glob.glob(os.path.join(output_import_path, "*.scn"))
    if len(scenes) > 0:
        scene_file_name = os.path.splitext(os.path.basename(scenes[0]))[0]

    # the path go to export compiled
    scn_path = os.path.join(scene_folder_name, scene_file_name + ".scn")

    # Add it to the scene
    n = hl.CreateInstanceFromAssets(gVal.scene, hl.Mat4.Identity, scn_path, gVal.res, hl.GetForwardPipelineInfo())[0]

    # init physic
    if make_physics_object:
        for node in n.GetInstanceSceneView().GetNodes(gVal.scene):
            if node.HasObject() and not node.HasRigidBody():
                # test if node have .collision_bin file
                path = gVal.res.GetModelName(node.GetObject().GetModelRef())
                collision_mesh_path = path + ".physics_bullet"
                if not os.path.exists(os.path.join(output_assets_compiled_path, collision_mesh_path)):
                    print("Can't created collision mesh for node {}".format(node.GetName()))
                    continue

                # create collision mesh
                mesh_col = gVal.scene.CreateCollision()

                # check the type from the json
                mesh_col.SetType(collision_type)
                if os.path.exists(os.path.join(output_assets_path, path + ".physics")):
                    with open(os.path.join(output_assets_path, path + ".physics")) as f:
                        json_physic = json.load(f)
                        if "collision" in json_physic and "input" in json_physic["collision"]:
                            json_type = json_physic["collision"]["input"][0]
                            if "type" in json_type:
                                if json_type["type"] == "convex":
                                    mesh_col.SetType(hl.CT_MeshConvex)
                                elif json_type["type"] == "triangle":
                                    mesh_col.SetType(hl.CT_Mesh)

                mesh_col.SetCollisionResource(collision_mesh_path)
                mesh_col.SetMass(physic_mass)

                node.SetCollision(0, mesh_col)

                # create rigid body
                rb = gVal.scene.CreateRigidBody()
                rb.SetType(physic_type)
                rb.SetFriction(friction)
                rb.SetRollingFriction(rolling_friction)
                node.SetRigidBody(rb)

                gVal.physics.NodeCreatePhysicsFromAssets(node)

    return n


###############################################################################
# FLUSH AND RENDER
###############################################################################


def Flush3D():
    if len(gVal.models_3D) <= 0 and len(gVal.texts_3D) <= 0 and len(gVal.lines_3D) <= 0 and len(gVal.quads_3D) <= 0 and not gVal.debug_physics:
        return

    for id_pass, pass_view in enumerate(gVal.pass_views):
        view_id = hl.GetSceneForwardPipelinePassViewId(pass_view, hl.SFPP_Opaque)
        view_id_Transparent = hl.GetSceneForwardPipelinePassViewId(pass_view, hl.SFPP_Transparent)

        for model in gVal.models_3D:
            hl.DrawModel(view_id, model["mdl"], model["shader"], [], [], model["mat4"])

        for line in gVal.lines_3D:
            if len(line["v"]) > 0:
                vtx = hl.Vertices(gVal.vtx_layouts["PosFloatColorUInt8"], len(line["v"]))
                for index, (v, c) in enumerate(zip(line["v"], line["c"])):
                    vtx.Begin(index).SetPos(v).SetColor0(c).End()

                hl.DrawLines(view_id, vtx, gVal.shaders["pos_rgb"])

        # draw quad 3D
        for quad in gVal.quads_3D:
            texture_path = quad["tex_path"]

            # cache texture
            if texture_path is not None and texture_path not in gVal.CacheTexturePathToUniformTargetTex:
                target_tex = hl.LoadTextureFromAssets(texture_path, 0)[0]
                uniform_target_tex = hl.MakeUniformSetTexture("s_tex", target_tex, 0)
                gVal.CacheTexturePathToUniformTargetTex[texture_path] = uniform_target_tex

            quad_vtx = hl.Vertices(gVal.vtx_layouts["PosFloatTex0Float"], 4)
            quad_vtx.Begin(0).SetPos(quad["a"]).SetTexCoord0(hl.Vec2(0, 1)).End()
            quad_vtx.Begin(1).SetPos(quad["b"]).SetTexCoord0(hl.Vec2(0, 0)).End()
            quad_vtx.Begin(2).SetPos(quad["c"]).SetTexCoord0(hl.Vec2(1, 0)).End()
            quad_vtx.Begin(3).SetPos(quad["d"]).SetTexCoord0(hl.Vec2(1, 1)).End()
            quad_idx = [0, 3, 2, 0, 2, 1]

            # set the uniforms and call the render
            if texture_path is not None:
                hl.DrawTriangles(
                    view_id, quad_idx, quad_vtx, gVal.shaders["tex0"], [], [gVal.CacheTexturePathToUniformTargetTex[texture_path]], hl.ComputeRenderState(hl.BM_Alpha),
                )
            else:
                hl.DrawTriangles(
                    view_id,
                    quad_idx,
                    quad_vtx,
                    gVal.shaders["color"],
                    [hl.MakeUniformSetValue("u_simplecolor", hl.Vec4(quad["color_a"].r, quad["color_a"].g, quad["color_a"].b, quad["color_a"].a,),)],
                    [],
                    hl.ComputeRenderState(hl.BM_Opaque),
                )

        for t in gVal.texts_3D:
            hl.DrawText(
                view_id_Transparent, t["font"], t["t"], gVal.shaders["font"], "u_tex", 0, t["m"], hl.Vec3(0, 0, 0), hl.DTHA_Left, hl.DTVA_Top, [t["c"]], [], text_render_state,
            )

    if gVal.debug_physics:
        gVal.physics.RenderCollision(
            view_id, gVal.vtx_layouts["PosFloatColorUInt8"], gVal.shaders["pos_rgb"], hl.ComputeRenderState(hl.BM_Opaque, hl.DT_Always, hl.FC_Disabled), 0,
        )

    # clear everyone
    gVal.models_3D.clear()
    gVal.texts_3D.clear()
    gVal.lines_3D.clear()
    gVal.quads_3D.clear()


def Flush2D(view_id):
    if len(gVal.objects_2D) <= 0:
        return view_id

    # for all the framebuffer if there is VR
    framebuffers_size = [hl.Vec2(gVal.width, gVal.height)]
    framebuffers = [None]  # [env.render_targets[f"PipelineFrameBuffer{x}"].handle for x in range(len(env.cameras))]

    if gVal.activate_VR:
        framebuffers.append(gVal.vr_left_fb.GetHandle())
        framebuffers.append(gVal.vr_right_fb.GetHandle())

        framebuffers_size.append(hl.Vec2(gVal.vr_state.width, gVal.vr_state.height))
        framebuffers_size.append(hl.Vec2(gVal.vr_state.width, gVal.vr_state.height))

    for id_framebuffer, (framebuffer, framebuffer_size) in enumerate(zip(framebuffers, framebuffers_size)):
        # set 2D view
        if framebuffer is not None:
            hl.SetViewFrameBuffer(view_id, framebuffer)
        else:
            hl.SetViewFrameBuffer(view_id, hl.InvalidFrameBufferHandle)

        hl.SetViewRect(view_id, 0, 0, int(framebuffer_size.x), int(framebuffer_size.y))
        hl.SetViewClear(view_id, hl.CF_Depth, 0, 1.0, 0)

        vs = hl.ComputeOrthographicViewState(
            hl.TranslationMat4(hl.Vec3(framebuffer_size.x / 2, framebuffer_size.y / 2, 0)), framebuffer_size.y, 0.1, 100, hl.Vec2(framebuffer_size.x / framebuffer_size.y, 1),
        )
        hl.SetViewTransform(view_id, vs.view, vs.proj)

        # draw objects 2D
        sorted_objects = sorted(gVal.objects_2D, key=operator.itemgetter("depth"), reverse=True)
        for object in sorted_objects:
            if object["object_type"] == "text":
                hl.DrawText(
                    view_id, object["font"], object["t"], gVal.shaders["font"], "u_tex", 0, object["m"], hl.Vec3(0, 0, 0), hl.DTHA_Left, hl.DTVA_Top, [object["c"]], [], text_render_state,
                )

            elif object["object_type"] == "quad":
                # if not object["show_in_vr"] and ((env.render_scn and id_framebuffer > 0) or not env.render_scn):
                # 	continue

                pos_in_pixel = object["pos_in_pixel"]
                width = object["width"]
                height = object["height"]
                texture_path = object["tex_path"]
                color = object["color"]
                render_state = object["render_state"]
                depth = object["depth"]

                # cache texture
                if texture_path is not None and texture_path not in gVal.CacheTexturePathToUniformTargetTex:
                    target_tex = hl.LoadTextureFromAssets(texture_path, 0)[0]
                    uniform_target_tex = hl.MakeUniformSetTexture("s_tex", target_tex, 0)
                    gVal.CacheTexturePathToUniformTargetTex[texture_path] = uniform_target_tex

                mat = hl.TransformationMat4(hl.Vec3(pos_in_pixel.x, pos_in_pixel.y, depth), hl.Vec3(0, 0, 0), hl.Vec3(1, 1, 1),)

                pos = hl.GetT(mat)
                axis_x = hl.GetX(mat) * width / 2
                axis_y = hl.GetY(mat) * height / 2

                quad_vtx = hl.Vertices(gVal.vtx_layouts["PosFloatTex0Float"], 4)
                quad_vtx.Begin(0).SetPos(pos - axis_x - axis_y).SetTexCoord0(hl.Vec2(0, 1)).End()
                quad_vtx.Begin(1).SetPos(pos - axis_x + axis_y).SetTexCoord0(hl.Vec2(0, 0)).End()
                quad_vtx.Begin(2).SetPos(pos + axis_x + axis_y).SetTexCoord0(hl.Vec2(1, 0)).End()
                quad_vtx.Begin(3).SetPos(pos + axis_x - axis_y).SetTexCoord0(hl.Vec2(1, 1)).End()
                quad_idx = [0, 3, 2, 0, 2, 1]

                # set the uniforms and call the render
                if texture_path is not None:
                    hl.DrawTriangles(
                        view_id, quad_idx, quad_vtx, gVal.shaders["tex0"], [], [gVal.CacheTexturePathToUniformTargetTex[texture_path]], render_state,
                    )
                else:
                    hl.DrawTriangles(
                        view_id, quad_idx, quad_vtx, gVal.shaders["color"], [hl.MakeUniformSetValue("u_simplecolor", hl.Vec4(color.r, color.g, color.b, color.a),)], [], render_state,
                    )

        hl.Touch(view_id)
        view_id = view_id + 1

    # clear everyone
    gVal.objects_2D.clear()

    return view_id


def UpdateDraw():
    gVal.mouse.Update()
    gVal.keyboard.Update()

    gVal.dt = hl.TickClock()
    view_id = 0

    # update fps controller
    if gVal.update_fps_controller and not hl.ImGuiWantCaptureMouse():
        cam_pos = gVal.camera.GetTransform().GetPos()
        cam_rot = gVal.camera.GetTransform().GetRot()
        hl.FpsController(gVal.keyboard, gVal.mouse, cam_pos, cam_rot, gVal.cam_speed, gVal.dt)
        gVal.camera.GetTransform().SetPos(cam_pos)
        gVal.camera.GetTransform().SetRot(cam_rot)

    # update audio listener properties
    hl.SetListener(gVal.camera.GetTransform().GetWorld(), hl.Vec3(0, 0, 0))

    # update lod
    LOD_Manager.UpdateLod(gVal.camera.GetTransform().GetWorld())

    # update scene
    hl.SceneUpdateSystems(
        gVal.scene, gVal.clocks, gVal.dt, gVal.physics, hl.time_from_sec_f(1.0 / 60.0), 4,
    )

    # draw scene
    gVal.pass_views.clear()
    view_state = gVal.scene.ComputeCurrentCameraViewState(hl.ComputeAspectRatioX(gVal.width, gVal.height))

    pass_view = hl.SceneForwardPipelinePassViewId()

    view_id, pass_view = hl.PrepareSceneForwardPipelineCommonRenderData(view_id, gVal.scene, gVal.render_data, gVal.pipeline, gVal.res, pass_view)
    view_id, pass_view = hl.PrepareSceneForwardPipelineViewDependentRenderData(view_id, view_state, gVal.scene, gVal.render_data, gVal.pipeline, gVal.res, pass_view,)
    view_id, pass_view = hl.SubmitSceneToForwardPipeline(view_id, gVal.scene, hl.IntRect(0, 0, gVal.width, gVal.height), view_state, gVal.pipeline, gVal.render_data, gVal.res,)
    gVal.pass_views.append(pass_view)

    # VR
    if gVal.activate_VR:
        gVal.vr_state = hl.OpenVRGetState(gVal.ground_vr_mat, 0.01, 1000)
        left, right = hl.OpenVRStateToViewState(gVal.vr_state)
        vr_eye_rect = hl.IntRect(0, 0, gVal.vr_state.width, gVal.vr_state.height)

        # Prepare the left eye render data then draw to its framebuffer
        view_id, pass_view = hl.PrepareSceneForwardPipelineViewDependentRenderData(view_id, left, gVal.scene, gVal.render_data, gVal.pipeline, gVal.res, pass_view,)
        view_id, pass_view = hl.SubmitSceneToForwardPipeline(view_id, gVal.scene, vr_eye_rect, left, gVal.pipeline, gVal.render_data, gVal.res, gVal.vr_left_fb.GetHandle(),)
        gVal.pass_views.append(pass_view)

        # Prepare the right eye render data then draw to its framebuffer
        view_id, pass_view = hl.PrepareSceneForwardPipelineViewDependentRenderData(view_id, right, gVal.scene, gVal.render_data, gVal.pipeline, gVal.res, pass_view,)
        view_id, pass_view = hl.SubmitSceneToForwardPipeline(view_id, gVal.scene, vr_eye_rect, right, gVal.pipeline, gVal.render_data, gVal.res, gVal.vr_right_fb.GetHandle(),)
        gVal.pass_views.append(pass_view)

    # flush 3D model
    Flush3D()

    # flush 2D
    view_id = Flush2D(view_id)

    # draw imgui endframe
    hl.ImGuiEndFrame(view_id)

    # draw everything and show the result in the window
    hl.Frame()

    if gVal.activate_VR:
        hl.OpenVRSubmitFrame(gVal.vr_left_fb, gVal.vr_right_fb)
    hl.UpdateWindow(gVal.win)

    hl.ImGuiBeginFrame(
        gVal.width, gVal.height, gVal.dt, gVal.mouse.GetState(), gVal.keyboard.GetState(),
    )

    return hl.ReadKeyboard().Key(hl.K_Escape) or not hl.IsWindowOpen(gVal.win)


###############################################################################
# DRAW IMMEDIATE FUNCTIONS
###############################################################################


def DrawBox(
    x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, size_x: float = 1, size_y: float = 1, size_z: float = 1,
):
    """Draws a 3d box. Info : every Draw function is immediate and will not return any node object."""
    DrawBoxM(
        hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)), hl.Vec3(size_x, size_y, size_z),
    )


def DrawBoxM(m: hl.Mat4, size: hl.Vec3 = hl.Vec3(1, 1, 1)):
    hl.SetScale(m, size)
    gVal.models_3D.append(
        {"mdl": gVal.models["box"], "shader": gVal.shaders["mdl_no_pipeline"], "mat4": m,}
    )


def DrawPlane(
    x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, size_x: float = 1, size_z: float = 1,
):
    """Draws a 3d plane."""
    gVal.models_3D.append(
        {"mdl": gVal.models["plane"], "shader": gVal.shaders["mdl_no_pipeline"], "mat4": hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z), hl.Vec3(size_x, 1, size_z),),}
    )


def DrawGeo(
    geo, x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0, size_x: float = 1, size_y: float = 1, size_z: float = 1,
):
    """Draws a 3d geometry."""
    gVal.models_3D.append(
        {"mdl": geo, "shader": gVal.shaders["mdl_no_pipeline"], "mat4": hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z), hl.Vec3(size_x, size_y, size_z),),}
    )


def DrawQuad3D(
    a_x,
    a_y,
    a_z,
    b_x,
    b_y,
    b_z,
    c_x,
    c_y,
    c_z,
    d_x,
    d_y,
    d_z,
    uv_a=0,
    uv_b=0,
    uv_c=1,
    uv_d=1,
    tex_path: str = None,
    color_a: hl.Color = hl.Color.White,
    color_b: hl.Color = hl.Color.White,
    color_c: hl.Color = hl.Color.White,
    color_d: hl.Color = hl.Color.White,
):
    """Draws a 3d quad."""

    DrawQuad3DV(
        hl.Vec3(a_x, a_y, a_z), hl.Vec3(b_x, b_y, b_z), hl.Vec3(c_x, c_y, c_z), hl.Vec3(d_x, d_y, d_z), uv_a, uv_b, uv_c, uv_d, tex_path, color_a, color_b, color_c, color_d,
    )


def DrawQuad3DV(
    a,
    b,
    c,
    d,
    uv_a=0,
    uv_b=0,
    uv_c=1,
    uv_d=1,
    tex_path: str = None,
    color_a: hl.Color = hl.Color.White,
    color_b: hl.Color = hl.Color.White,
    color_c: hl.Color = hl.Color.White,
    color_d: hl.Color = hl.Color.White,
):
    gVal.quads_3D.append(
        {"a": a, "b": b, "c": c, "d": d, "uv_a": uv_a, "uv_b": uv_b, "uv_c": uv_c, "uv_d": uv_d, "tex_path": tex_path, "color_a": color_a, "color_b": color_b, "color_c": color_c, "color_d": color_d,}
    )


def DrawQuad2D(
    pos_in_pixel_x: float,
    pos_in_pixel_y: float,
    width: int,
    height: int,
    tex_path: str = None,
    color: hl.Color = hl.Color.White,
    render_state: hl.RenderState = hl.ComputeRenderState(hl.BM_Alpha, hl.DT_Disabled),
    depth: float = 0,
    show_in_vr: bool = True,
):
    """Draws a 2d quad."""
    gVal.objects_2D.append(
        {
            "pos_in_pixel": hl.Vec2(pos_in_pixel_x, pos_in_pixel_y),
            "width": width,
            "height": height,
            "depth": depth,
            "tex_path": tex_path,
            "color": color,
            "render_state": render_state,
            "show_in_vr": show_in_vr,
            "object_type": "quad",
        }
    )


def DrawText2D(
    text: str, pos_in_pixel_x: float, pos_in_pixel_y: float, size: float = 1.0, color: hl.Color = hl.Color.Green, text_centered: bool = False, font_: hl.Font = None, depth: float = 1,
):
    """Draws 2d text on screen (requires loading a font)."""
    mat = hl.TransformationMat4(hl.Vec3(pos_in_pixel_x, pos_in_pixel_y, depth), hl.Vec3(0, 0, 0), hl.Vec3(1, 1, 1) * (size * gVal.height / 64),)
    if text_centered:
        text_rect = hl.ComputeTextRect(gVal.font, text)
        mat = hl.TransformationMat4(
            hl.Vec3(pos_in_pixel_x - (text_rect.ex - text_rect.sx) * 0.5 * size, pos_in_pixel_y - (text_rect.ey - text_rect.sy) * 0.5 * size, 1,),
            hl.Vec3(0, 0, 0),
            hl.Vec3(1, 1, 1) * (size * gVal.height / 64),
        )

    DrawTextM(text, mat, size, color, False, font_, is_2d=True, depth=depth)


def DrawText(
    text: str,
    x: float,
    y: float,
    z: float,
    angle_x: float = 0,
    angle_y: float = 0,
    angle_z: float = 0,
    size: float = 0.01,
    color: hl.Color = hl.Color.Green,
    text_centered: bool = False,
    font_: hl.Font = None,
    is_2d: bool = False,
):
    """Draws 3d text."""

    mat = hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z))
    DrawTextM(text, mat, size, color, text_centered, font_, is_2d)


def DrawTextM(
    text: str, mat: hl.Mat4, size: float = 0.01, color: hl.Color = hl.Color.Green, text_centered: bool = False, font_: hl.Font = None, is_2d: bool = False, depth: float = 1,
):
    t = {
        "font": gVal.font,
        "t": text,
        "c": hl.MakeUniformSetValue("u_color", hl.Vec4(color.r, color.g, color.b, color.a)),
        "object_type": "text",
        "depth": depth,
    }

    if font_ is not None:
        t["font"] = font_

    if text_centered:
        text_rect = hl.ComputeTextRect(t["font"], text)
        mat = mat * hl.TranslationMat4(hl.Vec3(-(text_rect.ex - text_rect.sx) * 0.5, (text_rect.ey - text_rect.sy) * 0.5, 0,) * size)

    hl.SetS(mat, hl.Vec3(size, -size, size))

    t["m"] = mat
    if is_2d:
        gVal.objects_2D.append(t)
    else:
        gVal.texts_3D.append(t)


def DrawLine(
    a_x: float, a_y: float, a_z: float, b_x: float, b_y: float, b_z: float, color: hl.Color = hl.Color.White, color2: hl.Color = hl.Color.White,
):
    """Draws a 3d line."""
    DrawLineV(hl.Vec3(a_x, a_y, a_z), hl.Vec3(b_x, b_y, b_z), color, color2)


def DrawLineV(
    a: hl.Vec3, b: hl.Vec3, color: hl.Color = hl.Color.White, color2: hl.Color = hl.Color.White,
):
    if len(gVal.lines_3D) <= 0 or len(gVal.lines_3D[len(gVal.lines_3D) - 1]["v"]) > 64000:
        gVal.lines_3D.append({"v": [], "c": []})

    id_lines_buffer = len(gVal.lines_3D) - 1

    gVal.lines_3D[id_lines_buffer]["v"].append(a)
    gVal.lines_3D[id_lines_buffer]["v"].append(b)
    gVal.lines_3D[id_lines_buffer]["c"].append(color)
    gVal.lines_3D[id_lines_buffer]["c"].append(color2)


def DrawLineList(points, colors):
    if len(gVal.lines_3D) <= 0 or (len(gVal.lines_3D[len(gVal.lines_3D) - 1]["v"]) > 64000):
        gVal.lines_3D.append({"v": [], "c": []})

    id_lines_buffer = len(gVal.lines_3D) - 1

    for p in points:
        gVal.lines_3D[id_lines_buffer]["v"].append(p)
    for c in colors:
        gVal.lines_3D[id_lines_buffer]["c"].append(c)


def DrawCross(
    x: float, y: float, z: float, color: hl.Color = hl.Color.White, size: float = 0.5, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0,
):
    """Draws a 3d Cross."""
    DrawCrossV(hl.Vec3(x, y, z), color, size, hl.Vec3(angle_x, angle_y, angle_z))


def DrawCrossV(
    pos: hl.Vec3, color: hl.Color = hl.Color.White, size: float = 0.5, rot: hl.Vec3 = hl.Vec3(0, 0, 0),
):
    rot_m = hl.RotationMat3(rot.x, rot.y, rot.z)

    DrawLineV(
        hl.Vec3(pos.x - size, pos.y, pos.z), hl.Vec3(pos.x + size, pos.y, pos.z), color, color,
    )
    DrawLineV(
        hl.Vec3(pos.x, pos.y - size, pos.z), hl.Vec3(pos.x, pos.y + size, pos.z), color, color,
    )
    DrawLineV(
        hl.Vec3(pos.x, pos.y, pos.z - size), hl.Vec3(pos.x, pos.y, pos.z + size), color, color,
    )


###############################################################################
# MISCELLANEOUS
###############################################################################


def ReturnTrueEveryXSec(sec: float, name_event: str):
    """Draws a 3d Cross. Returns a *boolean*."""
    if name_event not in gVal.EventNameElapsedSec or gVal.EventNameElapsedSec[name_event] > sec:
        gVal.EventNameElapsedSec[name_event] = 0
        return True

    gVal.EventNameElapsedSec[name_event] += GetDTSec()
    return False


def GetDTSec():
    """Returns delta-time value in *float*."""
    return hl.time_to_sec_f(gVal.dt)


def SetCamSpeed(v):
    """Set camera velocity."""
    gVal.cam_speed = v


def GetCamSpeed():
    """Get camera velocity. Returns an *int*"""
    return gVal.cam_speed


def DestroyNode(node: hl.Node):
    """Destroys a node from the scene."""
    gVal.scene.DestroyNode(node)


def __update_physic_mat__(node: hl.Node):
    """Updates node physic rigidbody."""
    if node.HasInstance():
        gVal.scene.Update(0)
        for sub_node in node.GetInstanceSceneView().GetNodes(gVal.scene):
            if sub_node.HasRigidBody() and sub_node.GetRigidBody().GetType() != hl.RBT_Kinematic:
                gVal.physics.NodeCreatePhysicsFromAssets(sub_node)


def ResetWorldAndForce(
    node: hl.Node, x: float = 0, y: float = 0, z: float = 0, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0,
):
    ResetWorldAndForceM(node, hl.TransformationMat4(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z)))


def ResetWorldAndForceV(node: hl.Node, p: hl.Vec3, r: hl.Vec3):
    ResetWorldAndForceM(node, hl.TransformationMat4(p, r))


def ResetWorldAndForceM(node: hl.Node, v: hl.Mat4):
    if type(node) == LOD_Manager.LOD_node:
        node = node.GetNode()

    vT = hl.GetT(v)
    vR = hl.GetT(v)

    w = node.GetTransform().GetWorld()
    prev_vT = hl.GetT(w)
    prev_vR = hl.GetR(w)
    w = hl.TransformationMat4(vT, vR, hl.GetS(w))

    # don't update if the rigid body is in kinematic
    if node.HasRigidBody() and node.GetRigidBody().GetType() != hl.RBT_Kinematic:
        gVal.physics.NodeResetWorld(node, w)

    if node.HasInstance():
        for sub_node in node.GetInstanceSceneView().GetNodes(gVal.scene):
            if sub_node.HasRigidBody() and sub_node.GetRigidBody().GetType() != hl.RBT_Kinematic:
                sub_w = sub_node.GetTransform().GetWorld()
                sub_vT = hl.GetT(sub_w)
                sub_vR = hl.GetR(sub_w)
                sub_w = hl.TransformationMat4(sub_vT + (prev_vT - vT), sub_vR + (prev_vR - vR), hl.GetS(w))

                gVal.physics.NodeResetWorld(sub_node, sub_w)

    node.GetTransform().SetWorld(w)


def SetPosition(node: hl.Node, x: float = 0, y: float = 0, z: float = 0):
    """Set the position of a node."""
    SetPositionV(node, hl.Vec3(x, y, z))


def SetPositionV(node: hl.Node, v: hl.Vec3):
    if type(node) == LOD_Manager.LOD_node:
        node = node.GetNode()

    w = node.GetTransform().GetWorld()
    prev_v = hl.GetT(w)
    hl.SetT(w, v)

    # don't update if the rigid body is in kinematic
    if node.HasRigidBody() and node.GetRigidBody().GetType() != hl.RBT_Kinematic:
        gVal.physics.NodeTeleport(node, w)

    if node.HasInstance():
        for sub_node in node.GetInstanceSceneView().GetNodes(gVal.scene):
            if sub_node.HasRigidBody() and sub_node.GetRigidBody().GetType() != hl.RBT_Kinematic:
                sub_w = sub_node.GetTransform().GetWorld()
                sub_v = hl.GetT(sub_w)
                hl.SetT(sub_w, sub_v + (prev_v - v))

                gVal.physics.NodeTeleport(sub_node, sub_w)

    node.GetTransform().SetWorld(w)


def SetRotation(node: hl.Node, x: float = 0, y: float = 0, z: float = 0):
    """Set the rotation of a node."""
    SetRotationV(node, hl.Vec3(x, y, z))


def SetRotationV(node: hl.Node, v: hl.Vec3):
    if type(node) == LOD_Manager.LOD_node:
        node = node.GetNode()

    w = node.GetTransform().GetWorld()
    prev_v = hl.GetR(w)
    w = hl.TransformationMat4(hl.GetT(w), v, hl.GetS(w))

    # don't update if the rigid body is in kinematic
    if node.HasRigidBody() and node.GetRigidBody().GetType() != hl.RBT_Kinematic:
        gVal.physics.NodeTeleport(node, w)

    if node.HasInstance():
        for sub_node in node.GetInstanceSceneView().GetNodes(gVal.scene):
            if sub_node.HasRigidBody() and sub_node.GetRigidBody().GetType() != hl.RBT_Kinematic:
                sub_w = sub_node.GetTransform().GetWorld()
                sub_v = hl.GetR(sub_w)
                sub_w = hl.TransformationMat4(hl.GetT(w), sub_v + (prev_v - v), hl.GetS(w))

                gVal.physics.NodeTeleport(sub_node, sub_w)

    node.GetTransform().SetWorld(w)


def SetScale(node: hl.Node, x: float = 1, y: float = 1, z: float = 1):
    """Set the scale of a node."""
    SetScaleV(node, hl.Vec3(x, y, z))


def SetScaleV(node: hl.Node, v: hl.Vec3):
    if type(node) == LOD_Manager.LOD_node:
        node = node.GetNode()

    # don't update if the rigid body is in kinematic
    if node.HasRigidBody() and node.GetRigidBody().GetType() != hl.RBT_Kinematic:
        w = node.GetTransform().GetWorld()
        hl.SetS(w, v)
        gVal.physics.NodeTeleport(node, w)

    node.GetTransform().SetScale(v)
    __update_physic_mat__(node)


def SetMat4(node: hl.Node, m: hl.Mat4):
    """Set the matrix of a node."""
    node.GetTransform().SetWorld(m)
    __update_physic_mat__(node)


def SetDiffuseTexture(node: hl.Node, texture_path: str):
    """Set the diffuse texture of a node."""
    if not os.path.exists(os.path.join(output_assets_path, os.path.basename(texture_path))):
        # copy texture to internal resources, then assetc
        os.makedirs(os.path.join(output_assets_path, os.path.basename(texture_path)))
        shutil.copy(
            texture_path, os.path.join(output_assets_path, os.path.basename(texture_path)),
        )

        # launch assetc to compile the newly added
        execute_assetc(output_assets_path, output_assets_compiled_path)

    mat = node.GetObject().GetMaterial(0)
    texture_ref = hl.LoadTextureFromAssets(os.path.basename(texture_path), 0, gVal.res)
    hl.SetMaterialTexture(mat, "uBaseOpacityMap", texture_ref, 0)


def KeyPressed(key: int):
    """Key pressed event, returns a *boolean*."""
    return gVal.keyboard.Pressed(key)


def KeyDown(key: int):
    """Key down event, returns a *boolean*."""
    return gVal.keyboard.Down(key)


def GetCameraMat4():
    """Get camera matrix 4. Returns *harfang.Mat4*."""
    return gVal.camera.GetTransform().GetWorld()


def NodeAddImpulse(node: hl.Node, dt_velocity: hl.Vec3, world_pos: hl.Vec3 = None):
    """Adds a physic impulse to a node."""
    if world_pos is not None:
        gVal.physics.NodeAddImpulse(node, dt_velocity, world_pos)
    else:
        gVal.physics.NodeAddImpulse(node, dt_velocity)


def NodeAddForce(node: hl.Node, F: hl.Vec3, world_pos: hl.Vec3 = None):
    """Adds force to a physic node."""
    if world_pos is not None:
        gVal.physics.NodeAddForce(node, F, world_pos)
    else:
        gVal.physics.NodeAddForce(node, F)


def SetParent(node: hl.Node, parentNode: hl.Node):
    """Adds a parent node to a node."""
    node.GetTransform().SetParent(parentNode)


###############################################################################
# VR
###############################################################################


def SetVRGroundAnchor(
    x: float, y: float, z: float, angle_x: float = 0, angle_y: float = 0, angle_z: float = 0,
):
    """Sets the VR Ground Anchor."""
    SetVRGroundAnchorV(hl.Vec3(x, y, z), hl.Vec3(angle_x, angle_y, angle_z))


def SetVRGroundAnchorV(p: hl.Vec3, r: hl.Vec3):
    gVal.ground_vr_mat = hl.TransformationMat4(p, r)


def GetVRControllersMat():
    """Get VR Controllers Matrix. Returns *harfang.Mat4*."""
    controllers_mat = []

    if not gVal.activate_VR:
        return controllers_mat

    # Get the matrix from the connected controllers
    vr_controller_names = hl.GetVRControllerNames()
    for n in vr_controller_names:
        if n not in gVal.vr_controllers:
            controller = hl.VRController(n)
            gVal.vr_controllers[n] = controller

        controller = gVal.vr_controllers[n]
        controller.Update()
        if controller.IsConnected():
            controller_mat = controller.World()
            controllers_mat.append(controller_mat)
    return controllers_mat


def Uninit():
    """Uninit Harfang High Level, destroys scene and window."""
    hl.RenderShutdown()
    hl.DestroyWindow(gVal.win)


###############################################################################
# SOUND
###############################################################################


def PlaySound(file_path: str, repeat: bool = False, volume: float = 1, mat: hl.Mat4 = None):
    """Plays a sound."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".wav" or ext == ".ogg":
        if ext == ".wav":
            snd_ref = hl.LoadWAVSoundAsset(file_path)  # WAV 44.1kHz 16bit mono
        if ext == ".ogg":
            snd_ref = hl.LoadOGGSoundAsset(file_path)

        if mat is not None:
            return hl.PlaySpatialized(snd_ref, hl.SpatializedSourceState(mat, volume, hl.SR_Loop if repeat else hl.SR_Once),)
        else:
            return hl.PlayStereo(snd_ref, hl.StereoSourceState(volume, hl.SR_Loop if repeat else hl.SR_Once),)

    print(f"ERROR SOUND: Can't handle extension {ext} from {file_path}")
    return None
