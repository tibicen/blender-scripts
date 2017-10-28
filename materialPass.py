import colorsys
from random import random, randrange, uniform

import bpy

bl_info = {
    "name": "MatPASS",
    "description": "Create one MaterialPass\LayerPass ImageNode in Compositor.",
    "author": "Dawid Huczynski",
    "version": (0, 5),
    "blender": (2, 67, 1),
    "location": "Proporieties > Render Layers > Material Pass",
    "warning": "",  # used for warning icon and text in addons panel
    # TODO change to blender wiki url
    "wiki_url": "https://github.com/tibicen/blender-scripts",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Render"
}

DEBUG = False
RANDOM_TEST_NR = randrange(0, 500)

# TEST ENV #########################################


def createMat():
    bpy.data.scenes[0].render.engine = 'CYCLES'
    for obj in bpy.data.objects:
        if obj.type == 'MESH' or obj.type == 'CURVE':
            obj.select = True
            MAT = bpy.data.materials.new('Mat')
            MAT.use_nodes = True
            MAT.diffuse_color = (random(), random(), random())
            obj.data.materials.append(MAT)
            obj.select = False


def create_scene():
    D = bpy.data
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for typ in (D.objects, D.materials, D.meshes):
        for el in typ:
            typ.remove(el, do_unlink=True)
    locations = []
    OFFSET = 3
    RANDOM_LOSS = False
    ROWS = 10
    for x in range(0, ROWS):
        for y in range(0, ROWS):
            for z in range(1):
                if randrange(0, 2) or not RANDOM_LOSS:
                    loc = (x * OFFSET + random() - .5, y * OFFSET +
                           random() - .5, 1 + z * OFFSET + random() - .1)
                    locations.append(loc)
    for nr, loc in enumerate(locations):
        bpy.ops.mesh.primitive_cube_add(location=(loc))
        obj = bpy.data.scenes[0].objects.active
        lays = [False for x in range(19)]
        lays.insert(1 + int(nr // (ROWS**2 / 20)), True)
        obj.layers = lays
    createMat()
    bpy.ops.object.camera_add(location=(-20, -20, 35),
                              rotation=(0.9, -0.0, -0.8))
    bpy.context.active_object.data.clip_end = 500

####################################################


def get_visible_materials():
    materials = []
    active_layers = bpy.data.scenes[0].layers
    for obj in bpy.data.objects:
        layer_comparison = list(zip(list(obj.layers),
                                    list(bpy.data.scenes[0].layers)))
        if sum([a and b for a, b in layer_comparison]):
            for slot in obj.material_slots:
                if slot.material not in materials:
                    if slot.material is not None:
                        materials.append(slot.material)
    return materials


def asign_material_indexes(color=True, only_visible=False):
    # TODO recreate colors from nodes: hue >> modulo >> *1.5 >> sat&val
    if not only_visible:
        materials = bpy.data.materials
    else:
        materials = get_visible_materials()
    indexes = [False if x.pass_index ==
               0 else True for x in materials]
    if sum(indexes) < len(materials):
        MatQuant = len(materials)
        k = 1 / float(MatQuant)
        for n, mat in enumerate(materials):
            mat.use_nodes = True
            mat.pass_index = n + 1
            if color:
                # Color tries to copy the colorramp color from the matpass
                mat.diffuse_color = colorsys.hsv_to_rgb(
                    .07 + n * k * 0.93, 1, .7 + .3 * (n % 2))


def asign_object_indexes(only_visible=False):
    for obj in bpy.data.objects:
        for nr, layer in enumerate(obj.layers):
            if layer:
                obj.pass_index = nr + 1


def create_color_var_nodes(node_group, count):
    ''' New solution for adding color in nodeTree O(0) instead of O(1)
        Instead of generating nodeTree of with node color for every material
        it generates colorramp and small saturation and value variations.
        Easier to manipulate, and possible to change color ramp variations.
    '''
    In = node_group.nodes.new('NodeGroupInput')
    In.location = (0, 0)
    In.name = 'In'
    Out = node_group.nodes.new('NodeGroupOutput')
    Out.name = 'Out'
    Out.location = (900, 0)
    # DIVIDE BY materials len (normalize [0:1])
    divide = node_group.nodes.new("CompositorNodeMath")
    divide.name = 'Divide'
    divide.location = (200, 0)
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = count
    node_group.links.new(divide.inputs[0], In.outputs[0])
    # ADD colors
    colorRamp = node_group.nodes.new("CompositorNodeValToRGB")
    colorRamp.name = 'colorRamp'
    colorRamp.location = (400, 160)
    # Creating color variations for every hue value
    colorRamp.color_ramp.color_mode = 'HSV'
    colorRamp.color_ramp.hue_interpolation = 'CW'
    r, g, b = colorsys.hsv_to_rgb(.07, 1, 1)
    colorRamp.color_ramp.elements[0].color = (r, g, b, 1)
    colorRamp.color_ramp.elements[0].position
    colorRamp.color_ramp.elements[1].color = (1, 0, 0, 1)
    # adding white element in the begining for white background
    colorRamp.color_ramp.elements.new(0)
    colorRamp.color_ramp.elements[0].color = (1, 1, 1, 1)
    node_group.links.new(colorRamp.inputs[0], divide.outputs[0])
    # every second value variation
    modulo = node_group.nodes.new("CompositorNodeMath")
    modulo.name = 'modulo'
    modulo.location = (200, -160)
    modulo.operation = 'MODULO'
    modulo.inputs[1].default_value = 2
    node_group.links.new(modulo.inputs[0], In.outputs[0])
    hsv = node_group.nodes.new("CompositorNodeHueSat")
    hsv.location = (700, 0)
    hsv.color_value = .9
    # TODO every third saturation variation
    node_group.links.new(hsv.inputs[0], modulo.outputs[0])
    node_group.links.new(hsv.inputs[1], colorRamp.outputs[0])
    node_group.links.new(Out.inputs[0], hsv.outputs[0])


def create_nodegroup_matpass():
    ''' Creates MateriaPASS for Compositor.'''
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Scene.render.layers[0].use_pass_material_index = True
    Scene.render.layers[0].pass_alpha_threshold = .001
    Tree = Scene.node_tree
    Src = Tree.nodes["Render Layers"]
    if bpy.data.scenes[0].matpass_settings.onlyVisible:
        materials = get_visible_materials()
    else:
        materials = bpy.data.materials
    MatQuant = len(materials)
    if 'MatPASS' in bpy.data.node_groups.keys():
        MatPASS = bpy.data.node_groups['MatPASS']
        MatPASS.nodes['Divide'].inputs[1].default_value = MatQuant
    else:
        MatPassGroup = bpy.data.node_groups.new(
            "MatPASS", type='CompositorNodeTree')
        MatPassGroup.name = 'MatPASS'
        create_color_var_nodes(MatPassGroup, MatQuant)
    if 'MatPASS' not in Tree.nodes.keys():
        # Adds to Group to render node tree
        MatPassNode = Tree.nodes.new('CompositorNodeGroup')
        MatPassNode.node_tree = bpy.data.node_groups['MatPASS']
        MatPassNode.name = 'MatPASS'
        x, y = Src.location
        MatPassNode.location = (x + 200, y - 320)
        Tree.links.new(MatPassNode.inputs[0], Src.outputs['IndexMA'])


def create_nodegroup_layerpass():
    ''' Creates LayerPASS for Compositor.'''
    Scene = bpy.context.scene
    Scene.use_nodes = True
    Tree = Scene.node_tree
    Scene.render.layers[0].use_pass_object_index = True
    Scene.render.layers[0].pass_alpha_threshold = .001
    Src = Tree.nodes["Render Layers"]
    LAYERS_LEN = 20
    k = 1 / float(LAYERS_LEN)
    LayPassGroup = bpy.data.node_groups.new(
        "LayerPASS", type='CompositorNodeTree')
    create_color_var_nodes(LayPassGroup, LAYERS_LEN)
    if 'LayerPASS' not in Tree.nodes.keys():
        # Adds to Group to render node tree
        LayPassNode = Tree.nodes.new('CompositorNodeGroup')
        LayPassNode.node_tree = bpy.data.node_groups['LayerPASS']
        LayPassNode.name = 'LayerPASS'
        x, y = Src.location
        LayPassNode.location = (x + 200, y - 200)
        Tree.links.new(LayPassNode.inputs[0], Src.outputs['IndexOB'])


def view_object_layers():
    STORAGE = {}
    for obj in bpy.data.objects:
        STORAGE[obj.name] = obj.diff


class createMattPass(bpy.types.Operator):
    """Create Material Pass for Compositor."""
    bl_idname = "material.matpass"
    bl_label = "Create MatPass"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if len(bpy.data.materials) == 0:
            raise(ZeroDivisionError)
        color = bpy.data.scenes[0].matpass_settings.colorBool
        only_visible = bpy.data.scenes[0].matpass_settings.onlyVisible
        if color:
            print('color')
        asign_material_indexes(color, only_visible)
        create_nodegroup_matpass()
        return {'FINISHED'}


class createLayerPass(bpy.types.Operator):
    """Create LAyer Pass for Compositor."""
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
    colorBool = bpy.props.BoolProperty(name="Replace viewport material colors",
                                       description="A simple bool property",
                                       default=False)
    onlyVisible = bpy.props.BoolProperty(name="Only visible",
                                         description="A simple bool property",
                                         default=False)


class MatPassPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window."""
    bl_label = 'Material Pass'
    bl_idname = 'RENDERLAYER_PT_material_pass'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render_layer'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if bpy.data.scenes[0].matpass_settings.onlyVisible:
            materials = get_visible_materials()
        else:
            materials = bpy.data.materials
        allMat = len(materials)
        activeMat = len([x for x in materials if x.users])
        row.label(text="There are {}/{} active materials.".format(
            activeMat, allMat), icon='MATERIAL_DATA')
        row = layout.row()
        row.prop(bpy.data.scenes[0].matpass_settings, "colorBool")
        row = layout.row()
        row.prop(bpy.data.scenes[0].matpass_settings, "onlyVisible")
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
    if DEBUG:
        create_scene()
