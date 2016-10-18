import colorsys
from random import random, randrange, uniform

import bpy

bl_info = {
    "name": "MatPASS",
    "description": "Create one MaterialPass ImageNode in Compositor.",
    "author": "Dawid Huczynski",
    "version": (0, 2),
    "blender": (2, 67, 1),
    "location": "View3D > Add > Mesh",
    "warning": "",  # used for warning icon and text in addons panel
    # TODO change to blender wiki url
    "wiki_url": "https://github.com/tibicen/blender-scripts",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Render"
}


# TEST UNITS CODE:#############################################################
RANDOM_TEST_NR = randrange(0, 500)

def createMat():
    bpy.data.scenes[0].render.engine = 'CYCLES'
    for obj in bpy.data.objects:
        if obj.type == 'MESH' or obj.type == 'CURVE':
            obj.select = True
            MAT = bpy.data.materials.new('Mat')
            MAT.use_nodes = True
            obj.data.materials.append(MAT)
            obj.select = False


class RandomCubes(bpy.types.Operator):
    """Create random objects test case"""
    bl_idname = "object.random_cubes"
    bl_label = "Create Random Cubes"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        locations = []
        xRows = bpy.data.scenes[0].matpass_settings.xRows
        for x in range(0, xRows):
            for y in range(0, xRows):
                for z in range(1):
                    if randrange(0, 2):
                        loc = (x * 2.5 + random() - .5, y * 2.5 +
                               random() - .5, z * 2.5 + random() - .5)
                        locations.append(loc)
        for loc in locations:
            bpy.ops.mesh.primitive_cube_add(location=(loc))
            obj = bpy.data.scenes[0].objects.active
            lays = [False for x in range(19)]
            lays.insert(randrange(0, 20), True)
            obj.layers = lays
        createMat()
        return {'FINISHED'}
###############################################################################


def asign_material_indexes(color=True):
    indexes = [False if x.pass_index ==
               0 else True for x in bpy.data.materials]
    if sum(indexes) < len(bpy.data.materials):
        MatQuant = len(bpy.data.materials)
        k = 1 / float(MatQuant)
        for n, mat in enumerate(bpy.data.materials):
            mat.use_nodes = True
            mat.pass_index = n + 1
            if color:
                mat.diffuse_color = colorsys.hsv_to_rgb(
                    k * (n - 1), uniform(.2, .9), uniform(.1, 1))


def create_nodegroup_matpass():
    # TODO convert to grayscale image and pass it through color ramp
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Scene.render.layers[0].use_pass_material_index = True
    Tree = Scene.node_tree
    Src = Tree.nodes["Render Layers"]
    # Dst = Tree.nodes["Composite"]
    MatPassGroup = bpy.data.node_groups.new(
        "MatPASS", type='CompositorNodeTree')
    #
    In = MatPassGroup.nodes.new('NodeGroupInput')
    In.location = (0, 0)
    In.name = 'In'
    MatQuant = len(bpy.data.materials)
    k = 1 / float(MatQuant)
    #
    for n in range(MatQuant):
        ID = MatPassGroup.nodes.new('CompositorNodeIDMask')
        ID.index = n + 1
        ID.location = (200 + 200 * n, 150)
        ID.label = ID.name
        Mix = MatPassGroup.nodes.new('CompositorNodeMixRGB')
        Mix.location = (400 + 200 * n, 0)
        Mix.label = Mix.name
        r, g, b = colorsys.hsv_to_rgb(k * n, uniform(.2, 1), uniform(.1, 1))
        Mix.inputs[2].default_value = (r, g, b, 1)
        # connect nodes
        MatPassGroup.links.new(Mix.inputs[0], ID.outputs[0])
        MatPassGroup.links.new(ID.inputs[0], In.outputs[0])
        if n == 0:
            PrevMix = Mix
        else:
            MatPassGroup.links.new(Mix.inputs[1], PrevMix.outputs[0])
            PrevMix = Mix
    Out = MatPassGroup.nodes.new('NodeGroupOutput')
    Out.location = (200 * MatQuant + 200, 0)
    Out.name = 'Out'
    #
    MatPassGroup.links.new(Out.inputs[0], Mix.outputs[0])
    #
    MatPassNode = Tree.nodes.new('CompositorNodeGroup')
    MatPassNode.node_tree = bpy.data.node_groups['MatPASS']
    x, y = Src.location
    MatPassNode.location = (x + 500, y - 500)
    Tree.links.new(MatPassNode.inputs[0], Src.outputs['IndexMA'])


def asign_object_indexes():
    for obj in bpy.data.objects:
        for nr, layer in enumerate(obj.layers):
            if layer:
                obj.pass_index = nr


def create_nodegroup_objpass():
    # TODO convert to operator
    # TODO convert to grayscale image and pass it through color ramp
    # TODO each layer with different HUE, each object on layer in different
    # saturation
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Tree = Scene.node_tree
    Scene.render.layers[0].use_pass_object_index = True
    Src = Tree.nodes["Render Layers"]
    # Dst = Tree.nodes["Composite"]
    ObjPassGroup = bpy.data.node_groups.new(
        "ObjPASS", type='CompositorNodeTree')
    #
    In = ObjPassGroup.nodes.new('NodeGroupInput')
    In.location = (0, 0)
    In.name = 'In'
    LAYERS_LEN = 20
    k = 1 / float(LAYERS_LEN)
    for n in range(LAYERS_LEN):
        ID = ObjPassGroup.nodes.new('CompositorNodeIDMask')
        ID.index = n + 1
        ID.location = (200 + 200 * n, 150)
        ID.label = ID.name
        Mix = ObjPassGroup.nodes.new('CompositorNodeMixRGB')
        Mix.location = (400 + 200 * n, 0)
        Mix.label = Mix.name
        r, g, b = colorsys.hsv_to_rgb(k * n, uniform(.2, 1), uniform(.1, 1))
        Mix.inputs[2].default_value = (r, g, b, 1)
        # connect nodes
        ObjPassGroup.links.new(Mix.inputs[0], ID.outputs[0])
        ObjPassGroup.links.new(ID.inputs[0], In.outputs[0])
        if n == 0:
            PrevMix = Mix
        else:
            ObjPassGroup.links.new(Mix.inputs[1], PrevMix.outputs[0])
            PrevMix = Mix
    Out = ObjPassGroup.nodes.new('NodeGroupOutput')
    Out.location = (200 * LAYERS_LEN + 200, 0)
    Out.name = 'Out'
    #
    ObjPassGroup.links.new(Out.inputs[0], Mix.outputs[0])
    #
    ObjPassNode = Tree.nodes.new('CompositorNodeGroup')
    ObjPassNode.node_tree = bpy.data.node_groups['ObjPASS']
    x, y = Src.location
    ObjPassNode.location = (x + 500, y - 390)
    Tree.links.new(ObjPassNode.inputs[0], Src.outputs['IndexOB'])


class createMattPass(bpy.types.Operator):
    """Create Material Pass for Compositor"""
    bl_idname = "material.matpass"
    bl_label = "Create MatPass"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        color = bpy.data.scenes[0].matpass_settings.colorBool
        if color:
            print('color')
        asign_material_indexes(color)
        create_nodegroup_matpass()
        return {'FINISHED'}


class createLayerPass(bpy.types.Operator):
    """Create Material Pass for Compositor"""
    bl_idname = "material.layerpass"
    bl_label = "Create LayerPass"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        asign_object_indexes()
        create_nodegroup_objpass()
        return {'FINISHED'}


class MatPassSettings(bpy.types.PropertyGroup):
    colorBool = bpy.props.BoolProperty(name="Generate viewport color",
                                       description="A simple bool property",
                                       default=True)
    xRows = bpy.props.IntProperty(name="xRows",
                                       description="A simple bool property",
                                       default=5)


class MatPassPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = 'Material Pass'
    bl_idname = 'RENDERLAYER_PT_material_pass'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render_layer'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text=str(RANDOM_TEST_NR), icon='WORLD_DATA')

        row = layout.row()
        allMat = len(bpy.data.materials)
        activeMat = len([x for x in bpy.data.materials if x.users])
        row.label(text="There are {} materials. {} of them are active".format(
            allMat, activeMat))
        row = layout.row()
        row.prop(bpy.data.scenes[0].matpass_settings, "xRows") #del
        row = layout.row()
        row.prop(bpy.data.scenes[0].matpass_settings, "colorBool")
        row = layout.row()
        row.operator("object.random_cubes") #del
        row = layout.row()
        row.operator("material.matpass")
        row = layout.row()
        row.operator("material.layerpass")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.matpass_settings = bpy.props.PointerProperty(
        type=MatPassSettings)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.matpass_settings

if __name__ == '__main__':
    register()
    # createMat()
    # asignIndexes(False)
    # addNodes()
    pass
