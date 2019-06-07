bl_info = {
    "name": "Molecule from PDB",
    "category": "Object",
}

import bpy
import bmesh
import mathutils
import math

import readpdb

ATOMSIZE = .5
BONDWIDTH = .2


class ObjectCursorArray(bpy.types.Operator):
    """Object Cursor Array"""
    bl_idname = "object.pdb2blend"
    bl_label = "Molecule from PDB"
    bl_options = {'REGISTER', 'UNDO'}

    total = bpy.props.FloatProperty(name="Scale", default=1, min=0.1, max=100)
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    highlight = bpy.props.StringProperty()


    def execute(self, context):
        # pdb = readpdb.PdbObject(self.filepath)
        pdb = readpdb.PdbObject('C:/Users/arrah/Desktop/OverLayCln5Se-PPPDE1/x.pdb')
        pdb.read()
        pdb.center()

        atomMat = makeMaterial('Atom',(1,0,0),(1,1,1),1)
        bondMat = makeMaterial('Atom',(.5,.5,.5),(1,1,1),1)

        vectors = []
        for i,pos in enumerate( pdb.iterBackBone()):
            vectors.append(pos)

        for code in self.highlight.split(':'):
            if not code:
                continue
            for i, atom in enumerate(pdb[int(code)]):
                pos = atom.position
                pos = mathutils.Vector(pos)
                name = str('RESI {}   ATOM '.format(code)+atom.name)
                bpy.ops.mesh.primitive_uv_sphere_add(location=pos, size=ATOMSIZE)
                setMaterial(bpy.context.object, atomMat)
                b_obj = bpy.data.objects[bpy.context.active_object.name]
                b_obj.name = name
                bpy.ops.object.shade_smooth()

            for a1, a2 in pdb[int(code)].iterBonds():
                name = 'RESI {} BOND  {} -- {}'.format(*([code]+[a for a in sorted([a1.name, a2.name])]))
                cylinder_between(*a1.position, *a2.position, BONDWIDTH, name=name, material=bondMat)


        MakePolyLine('bezier', 'curve', vectors)

        tor0refCirc = vecCircle("tor0refCirc", 6, 'CURVE')

        beziers = [o for o in bpy.data.objects if o.type == 'CURVE']

        for circleObj in beziers:
            circleName = circleObj.name
            circleObj.data.bevel_object = tor0refCirc

        createMaterial()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.operator(ObjectCursorArray.bl_idname)

# store keymaps here to access after registration
addon_keymaps = []


def register():
    bpy.utils.register_class(ObjectCursorArray)
    bpy.types.VIEW3D_MT_object.append(menu_func)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either, so we have to check this
    # to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(ObjectCursorArray.bl_idname, 'SPACE', 'PRESS', ctrl=True, shift=True)
        kmi.properties.total = 4
        addon_keymaps.append((km, kmi))

def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(ObjectCursorArray)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


# def MakePolyLine(objname, curvename, cList):
# #     curvedata = bpy.data.curves.new(name=curvename, type='CURVE')
# #     curvedata.dimensions = '3D'
# #     w = 1
# #
# #     objectdata = bpy.data.objects.new(objname, curvedata)
# #     objectdata.location = (0,0,0) #object origin
# #     bpy.context.scene.objects.link(objectdata)
# #
# #     polyline = curvedata.splines.new('BEZIER')
# #     polyline.bezier_points.add(len(cList)-1)
# #     for num in range(len(cList)):
# #         x, y, z = cList[num]
# #         lh = (cList[num-1] - cList[num])/2
# #         lh = lh + cList[num]
# #
# #         rh = (cList[(num+1)%len(cList)]  - cList[num])/2
# #         rh = rh + cList[num]
# #         polyline.bezier_points[num].co = cList[num]
# #         polyline.bezier_points[num].handle_left = lh
# #         polyline.bezier_points[num].handle_right = rh

def MakePolyLine(objname, curvename, cList):
    curvedata = bpy.data.curves.new(name=curvename, type='CURVE')
    curvedata.dimensions = '3D'
    w = 1

    objectdata = bpy.data.objects.new(objname, curvedata)
    objectdata.location = (0, 0, 0)  # object origin
    bpy.context.scene.objects.link(objectdata)

    polyline = curvedata.splines.new('NURBS')
    polyline.points.add(len(cList) - 1)
    for num in range(len(cList)):
        polyline.points[num].co = cList[num] + [w,]

    polyline.order_u = len(polyline.points) - 1
    polyline.use_endpoint_u = True


def cylinder_between(x1, y1, z1, x2, y2, z2, r, name='BOND', material=None):

  dx = x2 - x1
  dy = y2 - y1
  dz = z2 - z1
  dist = math.sqrt(dx**2 + dy**2 + dz**2)

  bpy.ops.mesh.primitive_cylinder_add(
      radius = r,
      depth = dist,
      location = (dx/2 + x1, dy/2 + y1, dz/2 + z1)
  )
  if material:
      setMaterial(bpy.context.object, material)

  phi = math.atan2(dy, dx)
  theta = math.acos(dz/dist)

  bpy.context.object.rotation_euler[1] = theta
  bpy.context.object.rotation_euler[2] = phi
  bpy.context.object.name = name


def vecCircle(name, verts, obj_type='MESH', radius=.2):
    bpy.ops.mesh.primitive_circle_add(vertices=verts, radius=radius)
    obj = bpy.context.active_object
    obj.name = name
    if obj_type == 'CURVE':
        bpy.ops.object.convert(target='CURVE', keep_original=False)
    return obj


def makeMaterial(name, diffuse, specular, alpha):

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat

def setMaterial(ob, mat):
    me = ob.data
    me.materials.append(mat)

def createMaterial():
    bpy.data.materials.new(name="BondMaterial")
    mat = bpy.data.materials['BondMaterial']
    # get the nodes
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # create emission node
    node_rgb = nodes.new(type='ShaderNodeRGB')
    node_rgb.color = (.4, .4, .4)
    node_rgb.location = 0, 0


    node_hue = nodes.new(type='ShaderNodeHueSaturation')
    node_hue.location = 400, 400
    node_hue.inputs[0].default_value = 1.  # Hue
    node_hue.inputs[1].default_value = .1 # Saturation
    node_hue.inputs[2].default_value = 1.1 # Value
    node_hue.inputs[3].default_value = 1 # Fac

    node_glass = nodes.new(type='ShaderNodeBsdfGlass')
    node_glass.location = 800, 400
    node_glass.inputs[1].default_value = 1.  # roughness
    node_glass.inputs[2].default_value = 1.450  # IOR


    # create output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 1200, 0

    links = mat.node_tree.links
    link = links.new(node_rgb.outputs[0], node_hue.inputs[4])
    link = links.new(node_hue.outputs[0], node_glass.inputs[0])
    link = links.new(node_glass.outputs[0], node_output.inputs[0])


if __name__ == "__main__":
    register()