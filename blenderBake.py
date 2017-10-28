# -*- coding: utf-8 -*-

import bpy

import datetime
import os
import math
import numpy as np
from threading import Thread

DEBUG = True
DEGREES = "\xb0"
FILEPATH = bpy.data.filepath.rsplit('\\', 1)[0]

os.chdir(FILEPATH)

resolution = 1024 * 2


data = {'resolution': (resolution, resolution)}


def level(x, lvl):
    return 0 if x < lvl else 1


level = np.vectorize(level)


def printd(text):
    if DEBUG:
        print(text)


def timeit(start=None, topic=''):
    if start is None:
        return datetime.datetime.now()
    else:
        end = datetime.datetime.now()
        printd('{}. Time: {}'.format(topic,
                                     round((end - start).seconds / 60, 6)))


def cleaning():
    tempIMG = []
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces[0].image = None
    # for uv in bpy.data.scenes[0].objects.active.data.uv_textures:
    #    if uv.name.startswith('shadow'):
    #        bpy.data.scenes[0].objects.active.data.uv_textures.remove(uv)
    for image in bpy.data.images:
        if image.name.startswith('shadow'):
            image.user_clear()
            tempIMG.append(image)
    for image in tempIMG:
        bpy.data.images.remove(image)


def scenePreparation():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            viewport = area.spaces[0]
    viewport.viewport_shade = 'MATERIAL'
    viewport.show_textured_shadeless = True
    for m in bpy.data.materials:
        m.use_nodes = True


def createImage(name):
    viewer_area = None
    viewer_space = None
    imgs = [i.name for i in bpy.data.images]
    if name in imgs:
        for image in bpy.data.images:
            if image.name == name:
                im = image
                break
    else:
        im = bpy.data.images.new(name,
                                 data['resolution'][0],
                                 data['resolution'][1],
                                 alpha=True)
    try:
        for area_search in bpy.context.screen.areas:
            if viewer_area is None and area_search.type == 'IMAGE_EDITOR':
                viewer_area = area_search
        for space in viewer_area.spaces:
            if space.type == "IMAGE_EDITOR":
                viewer_space = space
                viewer_space.image = im
                break
    except ValueError:
        raise(ValueError)
    return im


def bakeShadows(im):
    bpy.data.scenes[0].render.bake_type = 'FULL'
    bpy.data.scenes[0].render.bake_margin = 2
    # bpy.ops.object.bake_image()


def threaded_array(px, list):
    a = np.array(px)
    list.append(a)



def update_materials(obj, im):
    for slot in obj.material_slots:
        node_tree = slot.material.node_tree
        if 'Bake Texture' in node_tree.nodes.keys():
            node_tex = node_tree.nodes['Bake Texture']
        else:
            node_tex = node_tree.nodes.new(type='ShaderNodeTexImage')
        node_tex.image = im
        node_tex.label = 'Bake Texture'
        node_tex.name = 'Bake Texture'
        if 'Bake Shader' in node_tree.nodes.keys():
            node_emm = node_tree.nodes['Bake Shader']
        else:
            node_emm = node_tree.nodes.new(type='ShaderNodeEmission')
        node_emm.label = 'Bake Shader'
        node_emm.name = 'Bake Shader'
        node_tree.links.new(
            node_tex.outputs['Color'], node_emm.inputs['Color'])
        # node_tree.links.new(
        #     node_emm.outputs['Emission'], node_tree.nodes['Material Output'].inputs['Surface'])
        for node in node_tree.nodes:
            node.select = False
        node_tex.select = True


def bake_obj(obj, wm, smartUV=False):
    '''
    Creates separate shadow maps.
    '''
    name = 'baked-' + obj.name
    im = createImage(name)
    update_materials(obj, im)
    bpy.data.scenes[0].objects.active = obj
    obj.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    UVexists = False
    for uv in obj.data.uv_textures:
        if uv.name == 'bakeUV':
            UVexists = True
    if UVexists:
        obj.data.uv_textures["bakeUV"].active_render = True
    else:
        obj.data.uv_textures.new('bakeUV')
        obj.data.uv_textures["bakeUV"].active_render = True
        # obj.data.uv_textures['shadowUV'].data[0].image = im
        if smartUV:
            bpy.ops.uv.smart_project(angle_limit=66,
                                     island_margin=.05,
                                     user_area_weight=0)
        else:
            bpy.ops.uv.lightmap_pack(PREF_CONTEXT='SEL_FACES',
                                     PREF_PACK_IN_ONE=False,
                                     PREF_NEW_UVLAYER=False,
                                     PREF_APPLY_IMAGE=False,
                                     PREF_IMG_PX_SIZE=data['resolution'][0],
                                     PREF_BOX_DIV=12,
                                     PREF_MARGIN_DIV=.3)
    bpy.data.screens['UV Editing'].areas[1].spaces[0].image = im
    bpy.ops.object.mode_set(mode='OBJECT')
    ff = timeit()

    bpy.ops.object.select_all(action='DESELECT')
    # do rest for every object
    bpy.data.scenes[0].objects.active = obj
    obj.select = True
    bakeShadows(im)
    # th = Thread(target=threaded_array, args=(im.pixels, pxls_lst))
    timeit(ff, 'FULL LOOP')
    im.save_render(os.path.join(FILEPATH, 'bake_' +
                                obj.name + '.png'))
    return im


def bake_objs(objs):
    len_objs = len(objs)
    for nr, obj in enumerate(objs):
        print('\n\n### OBJECT {}/{} ###'.format(nr + 1, len_objs))
        total = timeit()
        wm = bpy.context.window_manager
        progressRange = 1000
        wm.progress_begin(0, progressRange)
        cleaning()
        im = bake_obj(obj, wm, smartUV=True)
        wm.progress_update(900)
        timeit(total, 'Total')
        wm.progress_end()




objs = bpy.context.selected_objects
bake_objs(objs)
bpy.data.scenes[0].render.engine = 'CYCLES'
for m in bpy.data.materials:
    m.use_nodes = True
