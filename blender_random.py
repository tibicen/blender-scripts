import random
import bpy
from mathutils import Vector

scene = bpy.context.scene

VOXEL_LIST = []  # for future implementation
TRIALS = 10
LENGTH = 500


def boolean(objA, objB):
    '''Union two objects and joins them together.'''
    boo = objA.modifiers.new('Booh', 'BOOLEAN')
    boo.object = objB
    boo.operation = 'UNION'
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Booh")
    scene.objects.unlink(objB)


# CREATE ALL MATERIALS AT ONCE
mat = bpy.data.materials.new('MAT')
mat.diffuse_color = (.9, .9, .9)
# materials = []
# for n in range(LENGTH):
#     mat = bpy.data.materials.new(str(n))
#     mat.diffuse_color = (0, n / float(LENGTH), 0)
#     materials.append(mat)
# CREATES FIRST OBJECT
loc = (0, 0, 0)
# obj = bpy.ops.mesh.primitive_cube_add(radius=.5, location=loc)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16,
                                     size=1, location=loc)
bpy.context.object.data.materials.append(mat)
bpy.ops.object.shade_smooth()
obj = bpy.data.scenes[0].objects.active

for n in range(TRIALS):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.scenes[0].objects.active = obj
    obj.select = True
    for n in range(1, LENGTH):
        # GENERATE NEXT LOCATION
        vec = Vector((random.random() * 2 - 1,
                      random.random() * 2 - 1,
                      random.random() * 2 - .95))
        vec.normalize()
        # loc = Vector(loc) + vec
        # loc = loc.to_tuple()
        # bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(1, 0, 0), "constraint_axis":(True, False, False), "constraint_orientation":'GLOBAL', "mirror":False, "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False})
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={"linked": True},
            TRANSFORM_OT_translate={"value": vec*1.5})
        # ASSIGN MATERIALS
        bpy.context.object.pass_index = n  # for different color variations
        # REFRESH VIEWPORT
        if n % 100 == 0:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            pass
