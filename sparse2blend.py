import math
import os
from struct import unpack as b2float
from shutil import copy2
import bpy

WORK_DIR = 'J:\\3d\\2017dojutra\\colmap'
FILE_NAME = 'model.ply'
focal_mm = 4.68
ROTATION_X = -90.0
ROTATION_Z = 84.5112488


os.chdir(WORK_DIR)


def copy_images(images):
    folder = 'seq_imgs'
    if 'seq_imgs' not in os.listdir():
        os.mkdir(folder)
    images = sorted(images)
    for nr, img in enumerate(images):
        name = os.path.split(img)[1]
        copy2(img, os.path.join(folder,'{:04d}.jpg'.format(nr)))




def bundle2points(ROTATION_X, ROTATION_Z):
    data = open('sparse.out.list.txt')
    t = data.read()
    data.close()
    camera_paths = [x for x in t.split('\n')[:-1]]
    if 'seq_imgs' not in os.listdir() or len(os.listdir('seq_imgs'))==0:
        copy_images(camera_paths)
    camera_names = [x.split('\\')[-1].rstrip('.jpg')
                    for x in t.split('\n')[:-1]]
    image = bpy.data.images.load(os.path.join(WORK_DIR, camera_paths[0]))
    render = bpy.data.scenes[0].render
    render.resolution_x, render.resolution_y = image.size
    pixel_width = max(image.size)
    data = open('sparse.out')
    t = data.read()
    data.close()
    lines = t.split('\n')[1:-1]
    cam_len, particles_len = [int(x) for x in lines.pop(0).split(' ')]
    cameras_data = []
    for nr,name  in enumerate(camera_names):
        focal_pixel = float(lines[0].split()[0])
        matrix = tuple([tuple([float(n) for n in x.split(' ')])
                        for x in lines[1 + nr * 5: 4 + nr * 5]])
        loc = tuple([float(n) for n in lines[4 + nr * 5].split(' ')])
        cameras_data.append((name, matrix, loc, focal_pixel))
    points_data = []
    for nr in range(cam_len * 5, len(lines), 3):
        loc = tuple([float(x) for x in lines[nr].split(' ')])
        rgb = tuple([int(x) for x in lines[nr + 1].split(' ')])
        points_data.append((loc, rgb))
    xrot = Matrix.Rotation(radians(ROTATION_X), 4, 'X')
    yrot = Matrix.Rotation(radians(-ROTATION_Z), 4, 'Y')
    locs = [x[0] for x in points_data]
    mesh = bpy.data.meshes.new('Sparse')
    mesh.from_pydata(locs, [], [])
    obj = bpy.data.objects.new('Sparse', mesh)
    bpy.context.scene.objects.link(obj)
    bpy.data.scenes[0].update()
    bpy.data.scenes[0].frame_end = len(camera_names)
    bpy.data.scenes[0].frame_start = 1
    obj.matrix_world = xrot * yrot
    for nr, d in enumerate(sorted(cameras_data, key=lambda x: x[0])):
        name, matrix, loc, focal_pixel = d
        cam = bpy.data.cameras.new('Camera {:03d} {}'.format(nr, name))
        cam.angle_x = math.atan(render.resolution_x /
                                (focal_pixel * 2.0)) * 2.0
        cam.angle_y = math.atan(render.resolution_y /
                                (focal_pixel * 2.0)) * 2.0
        cam_obj = bpy.data.objects.new('Camera {:03d} {}'.format(nr, name), cam)
        bpy.data.scenes[0].objects.link(cam_obj)
        marker = bpy.data.scenes[0].timeline_markers.new(str(nr+1), nr+1)
        marker.camera = cam_obj
        cam_obj.data.angle = 1.0956042040067078 #TODO automatic
        loc_mat = Vector(loc).to_4d()
        rot_mat = Matrix(matrix).to_4x4()
        rot_mat.transpose()
        p = -(rot_mat * loc_mat)
        p[3] = 1.0
        m = rot_mat.copy()
        m.col[3] = p
        cam_obj.matrix_world = xrot * yrot * m


# locs = [x[1] for x in cameras_data]
# mesh = bpy.data.meshes.new('Cam')
# mesh.from_pydata(locs, [], [])
# obj = bpy.data.objects.new('Cam', mesh)
# bpy.context.scene.objects.link(obj)
# bpy.data.scenes[0].update()


def colmap2planes(data_points):
    points = open('points3D.txt')
    t = points.read()
    lines = t.split('\n')[3:-1]
    data_points = [[float(n) for n in x.split(' ')[:7]] for x in lines]
    for point in data_points:
        bpy.ops.mesh.primitive_plane_add(radius=.02, location=point[
                                         1:4], rotation=[0, 0, 0])
        obj = bpy.data.objects['Plane']
        obj.name = 'point_{:d}'.format(int(point[0]))
        obj.data.vertex_colors.new('Col')
        for vert in obj.data.vertex_colors['Col'].data:
            vert.color = [x / 255 for x in point[4:7]]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.name.startswith('point_'):
            obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.join()


def colmap2vertex():
    points = open('points3D.txt')
    t = points.read()
    lines = t.split('\n')[3:-1]
    data_points = [[float(n) for n in x.split(' ')[1:4]] for x in lines]
    # ID X Y Z R G B
    # return data_points
    mesh = bpy.data.meshes.new('Sparse')
    mesh.from_pydata(data_points, [], [])
    obj = bpy.data.objects.new('Sparse', mesh)
    bpy.context.scene.objects.link(obj)
    bpy.data.scenes[0].update()


def colmap2particles():
    points = open('points3D.txt')
    t = points.read()
    lines = t.split('\n')[3:-1]
    data_points = [[float(n) for n in x.split(' ')[:7]] for x in lines]
    # ID X Y Z R G B
    # return data_points
    mesh = bpy.data.meshes.new('Sparse')
    mesh.from_pydata([(0, 0, 0), (0, 0, 0), (0, 0, 0),
                      (0, 0, 0)], [], [(0, 1, 2, 3)])
    bpy.ops.mesh.primitive_uv_sphere_add()
    sphere = bpy.data.objects['Sphere']
    obj = bpy.data.objects.new('Sparse', mesh)
    bpy.context.scene.objects.link(obj)
    modifier = obj.modifiers.new('Sparse', 'PARTICLE_SYSTEM')
    bpy.data.scenes[0].gravity = (0, 0, 0)
    psys = modifier.particle_system
    psys.name = 'Sparse'
    psett = psys.settings
    psett.count = len(data_points)
    psett.show_unborn = True
    psett.use_dead = True
    psett.use_render_emitter = False
    psett.lifetime = 100
    psett.frame_start = 0
    psett.frame_end = 0
    psett.physics_type = 'NO'
    psett.render_type = 'OBJECT'
    psett.dupli_object = sphere
    for nr in range(psett.count):
        psys.particles[nr].location = Vector(data_points[nr][1:4])
        # vert.color = [x / 255 for x in point[4:7]]
    bpy.data.scenes[0].update()


def colmap2camera():
    images = open('images.txt')
    t = images.read()
    lines = t.split('\n')[4::2][:-1]
    data_images = [x.split(' ') for x in lines]
    # data2mesh = [[float(n) for n in x.split(' ')[5:8]] for x in lines]
    # mesh = bpy.data.meshes.new('Cams')
    # mesh.from_pydata(data2mesh[:-1], [], [])
    # obj = bpy.data.objects.new('Cams', mesh)
    # bpy.context.scene.objects.link(obj)
    # bpy.data.scenes[0].update()
    for ver in data_images:
        # IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
        name = ver[-1].rstrip('.jpg')
        vect = [float(x) for x in ver[5:8]]
        quat = [float(x) for x in ver[1:5]]
        cam = bpy.data.cameras.new('Camera {}'.format(name))
        cam_obj = bpy.data.objects.new('Camera {}'.format(name), cam)
        bpy.data.scenes[0].objects.link(cam_obj)
        loc_mat = Matrix.Translation(Vector(vect))
        R_blender_cam = Matrix(((-1, 0, 0), (0, -1, 0), (0, 0, -1)))
        # XWZ-Y from wxyz
        quat = [quat[1], quat[0], quat[3], quat[2] * -1]
        cam_obj.location = vect
        cam_obj.rotation_mode = 'QUATERNION'
        cam_obj.rotation_quaternion = Quaternion(quat)
        rot_mat = (Quaternion(quat).to_matrix() * R_blender_cam).to_4x4()
        # scl_mat = Matrix.Scale(1,4,(1,0,0)) * Matrix.Scale(1,4,(0,1,0)) * Matrix.Scale(1,4,(0,0,1))
        # cam_obj.matrix_world = loc_mat * rot_mat


colmap2camera()


def gen_points(data_points):
    verts = read_data(FILE_NAME)
    f = open('data.txt', 'w')
    for n in verts:
        f.write(
            '{:f},{:f},{:f},{:f},{:f},{:f},{:d},{:d},{:d},{:d}\n'.format(*n))
    print('Exported.')
    f.close()
    f = open('data.txt')
    t = f.read()
    print(t[:120])
    f.close()
    lines = t.split('\n')[:-1]
    data = [[float(n) for n in x.split(',')] for x in lines]

    for nr, point in enumerate(data_points):
        bpy.ops.mesh.primitive_plane_add(radius=.02, location=point[
                                         0:3], rotation=point[3:6])
        obj = bpy.data.objects['Plane']
        obj.name = 'point_{:d}'.format(nr)
        obj.data.vertex_colors.new('Col')
        for vert in obj.data.vertex_colors['Col'].data:
            vert.color = [x / 255 for x in point[6:9]]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.name.startswith('point_'):
            obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.join()


def read_data(file_name):
    f = open(file_name, 'rb')
    t = f.read()
    print(t[:50])
    front, data = t.split(b'end_header\r\n')
    verts = [[b2float('<f', data[i:i + 4])[0],
              b2float('<f', data[i + 4:i + 8])[0],
              b2float('<f', data[i + 8:i + 12])[0],
              b2float('<f', data[i + 12: i + 16])[0],
              b2float('<f', data[i + 16:i + 20])[0],
              b2float('<f', data[i + 20:i + 24])[0],
              data[i + 24], data[i + 25], data[i + 26], data[i + 27]
              ] for i in range(0, len(data), 28)]
    for n in verts[:10]:
        print('\t'.join(['{:7.3f}'.format(x) for x in n]))
    print('Read.')
    return verts
