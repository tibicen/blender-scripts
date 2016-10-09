import random

import bpy

from mathutils import Vector

scene = bpy.context.scene

voxelList = []  # for future implementation
trials = 20
lenght = 500


# TODO create dict with all materials at once / optimize memory
materials = []
for n in range(lenght):
    mat = bpy.data.materials.new(str(n))
    mat.diffuse_color = (0, n / float(lenght), 0)
    materials.append(mat)
# TODO create one mesh to duplicate among objects / optimize memory

for n in range(trials):
    loc = (0, 0, 0)
    for n in range(lenght):
        # TODO get rid of if statement from loop
        if n == 0:
            loc = (0, 0, 0)
        else:
            vec = Vector((random.random() * 2 - 1,
                          random.random() * 2 - 1,
                          random.random() * 2 - .9))
            vec.normalize()
            loc = Vector(loc2) + vec
            loc = loc.to_tuple()

        obj = bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16,
                                                   size=1, location=loc)
        # obj = bpy.ops.mesh.primitive_cube_add(radius=.5, location=loc)
        # smooth object
        objA = scene.objects.active
        bpy.ops.object.shade_smooth()
        # assign material
        mat = bpy.data.materials.new(str(n))
        mat.diffuse_color = (0, n / float(lenght), 0)
        bpy.context.object.data.materials.append(mat)
        # if n > 0:
        #     boo = objA.modifiers.new('Booh', 'BOOLEAN')
        #     boo.object = objB
        #     boo.operation = 'UNION'
        #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Booh")
        #     scene.objects.unlink(objB)
        vec = Vector((random.random() * 2 - 1,
                      random.random() * 2 - 1,
                      random.random() * 2 - .9))
        vec.normalize()
        loc = Vector(loc) + vec
        loc = loc.to_tuple()
        objB = objA
        # refresh viewport
        if n % 10 == 0:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
