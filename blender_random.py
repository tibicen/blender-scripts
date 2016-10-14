import random

import bpy

from mathutils import Vector

scene = bpy.context.scene

VOXEL_LIST = []  # for future implementation
TRIALS = 1
LENGTH = 500


def boolean(objA, objB):
    '''Union two objects and joins them together.'''
    boo = objA.modifiers.new('Booh', 'BOOLEAN')
    boo.object = objB
    boo.operation = 'UNION'
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Booh")
    scene.objects.unlink(objB)


# CREATE ALL MATERIALS AT ONCE
# TODO create material nodes based on object index and color ramp

if bpy.data.materials.find('RAMP_MAT') >= 0:
    mat = bpy.data.materials[bpy.data.materials.find('RAMP_MAT')]
else:
    mat = bpy.data.materials.new('RAMP_MAT')
    mat.diffuse_color = (.9, .9, .9)
    mat.use_nodes = True
    tree = mat.node_tree
    for n in tree.nodes:
        tree.nodes.remove(n)
    obj_node = tree.nodes.new("ShaderNodeObjectInfo")
    math = tree.nodes.new("ShaderNodeMath")
    math.inputs[1].default_value = 1 / LENGTH
    math.operation = 'MULTIPLY'
    col_ramp = tree.nodes.new("ShaderNodeValToRGB")
    col_ramp.color_ramp.elements[0].color = 1, 0, 0, 1
    col_ramp.color_ramp.elements[1].color = 0.7914081, 1, 0, 1
    diff = tree.nodes.new("ShaderNodeBsdfDiffuse")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    math.location = 200, 0
    col_ramp.location = 400, 0
    diff.location = 700, 0
    out.location = 900, 0
    tree.links.new(math.inputs[0], obj_node.outputs[1])
    tree.links.new(col_ramp.inputs[0], math.outputs[0])
    tree.links.new(diff.inputs[0], col_ramp.outputs[0])
    tree.links.new(out.inputs[0], diff.outputs[0])
# materials = []
# for n in range(LENGTH):
#     mat = bpy.data.materials.new(str(n))
#     mat.diffuse_color = (0, n / float(LENGTH), 0)
#     materials.append(mat)
# CREATES FIRST OBJECT
loc = (0, 0, 0)
bpy.ops.mesh.primitive_cube_add(radius=.5, location=loc)
# bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16,
#                                      size=1, location=loc)
# bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(mat)
obj = bpy.data.scenes[0].objects.active

for n in range(TRIALS):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.scenes[0].objects.active = obj
    obj.select = True
    for n in range(1, LENGTH):
        # GENERATE NEXT LOCATION
        vec = Vector((random.random() * 2 - 1,
                      random.random() * 2 - 1,
                      random.random() * 2 - .9))
        vec.normalize()
        # loc = Vector(loc) + vec
        # loc = loc.to_tuple()
        # bpy.ops.object.duplicate_move_linked(
        #     OBJECT_OT_duplicate = {"linked": True, "mode": 'TRANSLATION'},
        #     TRANSFORM_OT_translate = {"value": (1, 0, 0),
        #                             "constraint_axis": (True, False, False),
        #                             "constraint_orientation": 'GLOBAL',
        #                             "mirror": False,
        #                             "proportional": 'DISABLED',
        #                             "proportional_edit_falloff": 'SMOOTH',
        #                             "proportional_size": 1,
        #                             "snap": False,
        #                             "snap_target": 'CLOSEST',
        #                             "snap_point": (0, 0, 0),
        #                             "snap_align": False,
        #                             "snap_normal": (0, 0, 0),
        #                             "gpencil_strokes": False,
        #                             "texture_space": False,
        #                             "remove_on_cancel": False,
        #                             "release_confirm": False})
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={"linked": True},
            TRANSFORM_OT_translate={"value": vec * 1})
        # ASSIGN MATERIALS
        bpy.context.object.pass_index = n  # for different color variations
        # REFRESH VIEWPORT
        if n % 100 == 0:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            pass
