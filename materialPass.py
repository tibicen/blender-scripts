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

DEBUG = True


# TEST #############################################################
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
        offset = 3
        randomLoss = bpy.data.scenes[0].matpass_settings.randomLoss
        xRows = bpy.data.scenes[0].matpass_settings.xRows
        for x in range(0, xRows):
            for y in range(0, xRows):
                for z in range(1):
                    if randrange(0, 2) or  not randomLoss:
                        loc = (x * offset+ random() - .5, y * offset+
                               random() - .5, 1 + z * offset + random() - .1)
                        locations.append(loc)
        for nr, loc in enumerate(locations):
            bpy.ops.mesh.primitive_cube_add(location=(loc))
            obj = bpy.data.scenes[0].objects.active
            lays = [False for x in range(19)]
            lays.insert(1+ int(nr//(xRows**2/20)), True)
            obj.layers = lays
        createMat()
        bpy.ops.object.camera_add(location=(-33, -33, 28), rotation=(1.25, 0, -.8))
        bpy.context.active_object.data.clip_end = 500
        return {'FINISHED'}
#########################################################################


def asign_material_indexes(color=True):
    # TODO recreate colors from nodes: hue >> modulo >> *1.5 >> sat&val
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


def create_nodegroup_matpass_deprecated():
    '''An old solution for generating colornodes on material ID.'''
    # TODO convert to grayscale image and pass it through color ramp
    # TODO if nodegroup is aready in scene, update nodegroup
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Scene.render.layers[0].use_pass_material_index = True
    Tree = Scene.node_tree
    Src = Tree.nodes["Render Layers"]
    # Dst = Tree.nodes["Composite"]
    MatQuant = len(bpy.data.materials)
    k = 1 / float(MatQuant)
    if 'MatPASS' in bpy.data.node_groups.keys():
        MatPassGroup = bpy.data.node_groups['MatPASS']
        In = MatPassGroup.nodes['In']
        Out = MatPassGroup.nodes['Out']
        for node in MatPassGroup.nodes:
            if node.name not in ('In', 'Out'):
                MatPassGroup.nodes.remove(node)
    else:
        MatPassGroup = bpy.data.node_groups.new(
            "MatPASS", type='CompositorNodeTree')
        In = MatPassGroup.nodes.new('NodeGroupInput')
        In.location = (0, 0)
        In.name = 'In'
        Out = MatPassGroup.nodes.new('NodeGroupOutput')
        Out.name = 'Out'
    Out.location = (200 * MatQuant + 200, 0)
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
    MatPassGroup.links.new(Out.inputs[0], Mix.outputs[0])
    if 'MatPASS' not in Tree.nodes.keys():
        MatPassNode = Tree.nodes.new('CompositorNodeGroup')
        MatPassNode.node_tree = bpy.data.node_groups['MatPASS']
        MatPassNode.name = 'MatPASS'
        x, y = Src.location
        MatPassNode.location = (x + 500, y - 500)
        Tree.links.new(MatPassNode.inputs[0], Src.outputs['IndexMA'])


def create_nodegroup_matpass():
    ''' New solution for adding color in nodeTree O(0) instead of O(1)
        Instead of generating nodeTree of with node color for every material
        it generates colorramp and small saturation and value variations.
        Easier to manipulate, and possible to change color ramp variations.
    '''
    # TODO Create Matpass Group
    # TODO if matpass in scene only edit its parameters
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Scene.render.layers[0].use_pass_material_index = True
    Tree = Scene.node_tree
    Src = Tree.nodes["Render Layers"]
    # Dst = Tree.nodes["Composite"]
    MatQuant = len(bpy.data.materials)
    MatPassGroup = bpy.data.node_groups.new("MatPASS", type='CompositorNodeTree')
    # DIVIDE BY materials len (normalize [0:1])
    divide = Tree.nodes.new("CompositorNodeMath")
    divide.location = (200,0)
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = MatQuant
    Tree.links.new(divide.inputs[0], Src.outputs['IndexMA'])
    # ADD colors
    colorRamp = Tree.nodes.new("CompositorNodeValToRGB")
    colorRamp.location = (400, 0)
    # Creating color variations for every hue value
    colorRamp.color_ramp.color_mode = 'HSV'
    colorRamp.color_ramp.hue_interpolation = 'CW'
    r, g, b = colorsys.hsv_to_rgb(.07, 1, 1)
    colorRamp.color_ramp.elements[0].color = (r,g,b,1)
    colorRamp.color_ramp.elements[0].position
    colorRamp.color_ramp.elements[1].color = (1,0,0,1)
    # adding white element in the begining for white background
    colorRamp.color_ramp.elements.new(0)
    colorRamp.color_ramp.elements[0].color = (1,1,1,1)
    Tree.links.new(colorRamp.inputs[0], divide.outputs[0])
    # variate colors by saturation and value
    modulo = Tree.nodes.new("CompositorNodeMath")
    modulo.location = (700, 0)
    modulo.operation = 'MODULO'
    modulo.inputs[0].default_value = MatQuant
    Tree.links.new(modulo.inputs[1], colorRamp.outputs[0])
    mtply = Tree.nodes.new("CompositorNodeMath")
    mtply.location = (900, 0)
    mtply.operation = 'MULTIPLY'
    mtply.inputs[1].default_value = 1.5
    Tree.links.new(mtply.inputs[0], modulo.outputs[0])
    hsv = Tree.nodes.new("CompositorNodeHueSat")
    hsv.location = (1100, 0)
    hsv.color_saturation = .8
    hsv.color_value = .8
    Tree.links.new(hsv.inputs[0], mtply.outputs[0])
    Tree.links.new(hsv.inputs[1], colorRamp.outputs[0])

def asign_object_indexes():
    for obj in bpy.data.objects:
        for nr, layer in enumerate(obj.layers):
            if layer:
                obj.pass_index = nr


def create_nodegroup_layerpass():
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
    LAYERS_LEN = 20
    k = 1 / float(LAYERS_LEN)
    if 'LayerPASS' in bpy.data.node_groups.keys():
        return True
    LayPassGroup = bpy.data.node_groups.new(
        "LayerPASS", type='CompositorNodeTree')
    In = LayPassGroup.nodes.new('NodeGroupInput')
    In.location = (0, 0)
    In.name = 'In'
    Out = LayPassGroup.nodes.new('NodeGroupOutput')
    Out.name = 'Out'
    Out.location = (200 * LAYERS_LEN + 200, 0)
    for n in range(LAYERS_LEN):
        ID = LayPassGroup.nodes.new('CompositorNodeIDMask')
        ID.index = n + 1
        ID.location = (200 + 200 * n, 150)
        ID.label = ID.name
        Mix = LayPassGroup.nodes.new('CompositorNodeMixRGB')
        Mix.location = (400 + 200 * n, 0)
        Mix.label = Mix.name
        r, g, b = colorsys.hsv_to_rgb(k * n, uniform(.9, 1), uniform(.9, 1))
        Mix.inputs[2].default_value = (r, g, b, 1)
        # connect nodes
        LayPassGroup.links.new(Mix.inputs[0], ID.outputs[0])
        LayPassGroup.links.new(ID.inputs[0], In.outputs[0])
        if n == 0:
            PrevMix = Mix
        else:
            LayPassGroup.links.new(Mix.inputs[1], PrevMix.outputs[0])
            PrevMix = Mix

    #
    LayPassGroup.links.new(Out.inputs[0], Mix.outputs[0])
    #
    LayPassNode = Tree.nodes.new('CompositorNodeGroup')
    LayPassNode.node_tree = bpy.data.node_groups['LayerPASS']
    x, y = Src.location
    LayPassNode.location = (x + 500, y - 390)
    Tree.links.new(LayPassNode.inputs[0], Src.outputs['IndexOB'])


class createMattPass(bpy.types.Operator):
    """Create Material Pass for Compositor"""
    bl_idname = "material.matpass"
    bl_label = "Create MatPass"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if len(bpy.data.materials) == 0:
            raise(ZeroDivisionError)
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
        create_nodegroup_layerpass()
        return {'FINISHED'}


class MatPassSettings(bpy.types.PropertyGroup):
    colorBool = bpy.props.BoolProperty(name="Generate viewport color",
                                       description="A simple bool property",
                                       default=True)
    randomLoss = bpy.props.BoolProperty(name="Random cubes loss",
                                       description="A simple bool property",
                                       default=False)
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
        row.prop(bpy.data.scenes[0].matpass_settings, "colorBool")
        row = layout.row()
        row.prop(bpy.data.scenes[0].matpass_settings, "randomLoss")
        if DEBUG:  # for testing purpose
            row = layout.row()
            row.prop(bpy.data.scenes[0].matpass_settings, "xRows")
            row = layout.row()
            row.operator("object.random_cubes")
        row = layout.row()
        if activeMat == 0:
            row.label(text='Unable to create MatPass.')
            row = layout.row()
            row.label(text='No materials in scene.')
        else:
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
