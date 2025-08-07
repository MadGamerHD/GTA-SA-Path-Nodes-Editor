bl_info = {
    "name": "GTA SA Path Nodes Editor",
    "author": "MadGamerHD",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Path Nodes",
    "category": "Import-Export",
    "description": "Import, edit, and export GTA SA path nodes with full data round-trip and in-UI editing",
}

import bpy
import os
import struct
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (
    StringProperty, IntProperty, FloatProperty,
    CollectionProperty
)
from bpy.types import Operator, Panel, PropertyGroup

# ----------------------------------------------------------------------------
#   Data PropertyGroups
# ----------------------------------------------------------------------------
class PathLink(PropertyGroup):
    target_index: IntProperty(name="Target Node Index")
    length: FloatProperty(name="Link Length")

class PathNodeData(PropertyGroup):
    name: StringProperty()
    x: FloatProperty(name="X", default=0.0)
    y: FloatProperty(name="Y", default=0.0)
    z: FloatProperty(name="Z", default=0.0)
    link_offset: IntProperty(name="Link Offset", default=0)
    area_id: IntProperty(name="Area ID", default=0)
    node_id: IntProperty(name="Node ID", default=0)
    width: IntProperty(name="Width", default=0, min=0, max=255)
    node_type: IntProperty(name="Type", default=1, min=0, max=255)
    flags: IntProperty(name="Flags", default=0)
    links: CollectionProperty(type=PathLink)

# ----------------------------------------------------------------------------
#   Utility: clear existing data
# ----------------------------------------------------------------------------

def clear_pathnodes(context):
    sc = context.scene
    if hasattr(sc, 'pathnodes'):
        sc.pathnodes.clear()
    coll = bpy.data.collections.get("PathNodes")
    if coll:
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)

# ----------------------------------------------------------------------------
#   Import Operator
# ----------------------------------------------------------------------------
class IMPORT_OT_pathnodes(Operator, ImportHelper):
    bl_idname = "pathnodes.import_dat"
    bl_label = "Import nodes.dat"
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        sc = context.scene
        clear_pathnodes(context)
        main_coll = bpy.data.collections.new("PathNodes")
        sc.collection.children.link(main_coll)

        filepath = self.filepath
        with open(filepath, 'rb') as f:
            total, numVeh, numPed, numCar, numLinks = struct.unpack('<IIIII', f.read(20))
            # read nodes
            nodes_raw = []
            for i in range(total):
                data = f.read(28)
                mem, unused, x, y, z, marker, link_off, area, nid, width, ntype, flags = struct.unpack('<II3hHHHHBBI', data)
                nodes_raw.append((x/8.0, y/8.0, z/8.0, link_off, area, nid, width, ntype, flags))
            # read links
            raw_links = [struct.unpack('<II', f.read(8)) for _ in range(numLinks)]

        # create nodes
        for idx, (x,y,z,link_off,area,nid,width,ntype,flags) in enumerate(nodes_raw):
            nd = sc.pathnodes.add()
            nd.name = f"Node_{idx}"
            nd.x, nd.y, nd.z = x, y, z
            nd.link_offset = link_off
            nd.area_id = area
            nd.node_id = nid
            nd.width = width
            nd.node_type = ntype
            nd.flags = flags
            # empty visual
            obj = bpy.data.objects.new(nd.name, None)
            obj.empty_display_type = 'ARROWS'
            obj.empty_display_size = 0.2
            obj.location = Vector((x, y, z))
            obj['is_pathnode'] = True
            main_coll.objects.link(obj)

        # assign links
        for src, tgt in raw_links:
            if src < 0 or tgt < 0 or src >= total or tgt >= total:
                continue
            nd = sc.pathnodes[src]
            ln = nd.links.add()
            ln.target_index = tgt
            # calculate actual length
            p1 = main_coll.objects.get(f"Node_{src}")
            p2 = main_coll.objects.get(f"Node_{tgt}")
            if p1 and p2:
                ln.length = (p1.location - p2.location).length

        self.report({'INFO'}, f"Imported {total} nodes, {numLinks} links.")
        return {'FINISHED'}

# ----------------------------------------------------------------------------
#   Export Operator
# ----------------------------------------------------------------------------
class EXPORT_OT_pathnodes(Operator, ExportHelper):
    bl_idname = "pathnodes.export_dat"
    bl_label = "Export nodes.dat"
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        sc = context.scene
        total = len(sc.pathnodes)
        # build link list
        links = []
        for nd in sc.pathnodes:
            idx = int(nd.name.split('_')[-1])
            for ln in nd.links:
                links.append((idx, ln.target_index))
        numLinks = len(links)
        # map node->outgoing
        node_map = {}
        for src,tgt in links:
            node_map.setdefault(src, []).append(tgt)

        with open(self.filepath, 'wb') as f:
            # header
            f.write(struct.pack('<IIIII', total, 0, 0, 0, numLinks))
            link_offset = 0
            for nd in sc.pathnodes:
                idx = int(nd.name.split('_')[-1])
                x = int(nd.x * 8)
                y = int(nd.y * 8)
                z = int(nd.z * 8)
                marker = 0x7FFE
                nl = node_map.get(idx, [])
                count = len(nl)
                # reconstruct flags: preserve high bits, update low nibble
                raw_flags = nd.flags
                flags = (raw_flags & ~0xF) | (count & 0xF)
                # pack
                f.write(struct.pack(
                    '<II3hHHHHBBI',
                    0, 0, x, y, z,
                    marker,
                    link_offset,
                    nd.area_id,
                    nd.node_id,
                    nd.width,
                    nd.node_type,
                    flags
                ))
                link_offset += count
            # write links
            for src,tgt in links:
                f.write(struct.pack('<II', src, tgt))

        self.report({'INFO'}, f"Exported {total} nodes, {numLinks} links.")
        return {'FINISHED'}

# ----------------------------------------------------------------------------
#   UI Panel
# ----------------------------------------------------------------------------
class PATHNODES_PT_panel(Panel):
    bl_label = "Path Nodes Editor"
    bl_idname = "PATHNODES_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Path Nodes'

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        col = layout.column()
        col.operator(IMPORT_OT_pathnodes.bl_idname, icon='IMPORT')
        col.operator(EXPORT_OT_pathnodes.bl_idname, icon='EXPORT')
        layout.separator()
        layout.template_list("UI_UL_list", "pathnodes_list", sc, "pathnodes", sc, "active_pathnode")
        if sc.pathnodes:
            nd = sc.pathnodes[sc.active_pathnode]
            box = layout.box()
            box.prop(nd, "x"); box.prop(nd, "y"); box.prop(nd, "z")
            box.prop(nd, "area_id"); box.prop(nd, "node_id")
            box.prop(nd, "width"); box.prop(nd, "node_type")
            box.prop(nd, "flags")
            box.label(text=f"Link Offset: {nd.link_offset}")
            box.label(text=f"Links ({len(nd.links)}):")
            for ln in nd.links:
                box.label(text=f"→ {ln.target_index} ({ln.length:.2f})")

# ----------------------------------------------------------------------------
#   Registration
# ----------------------------------------------------------------------------
classes = [
    PathLink, PathNodeData,
    IMPORT_OT_pathnodes, EXPORT_OT_pathnodes,
    PATHNODES_PT_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pathnodes = CollectionProperty(type=PathNodeData)
    bpy.types.Scene.active_pathnode = IntProperty(default=0)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.pathnodes
    del bpy.types.Scene.active_pathnode

if __name__ == '__main__':
    register()
