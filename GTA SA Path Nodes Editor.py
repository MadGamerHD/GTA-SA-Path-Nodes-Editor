bl_info = {
    "name": "GTA SA Path Nodes Editor",
    "author": "MadGamerHD",
    "version": (1, 0, 4),
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
#   File-item for import dialog
# ----------------------------------------------------------------------------
class PathNodeFileItem(PropertyGroup):
    name: StringProperty(name="File Name")

# ----------------------------------------------------------------------------
#   Data PropertyGroups
# ----------------------------------------------------------------------------
class PathLink(PropertyGroup):
    target_index: IntProperty(name="Target Node Index")
    length: FloatProperty(name="Link Length")

class PathCarLink(PropertyGroup):
    dir_x: FloatProperty(name="Dir X")
    dir_y: FloatProperty(name="Dir Y")
    width: FloatProperty(name="Width")
    num_left_lanes: IntProperty(name="Left Lanes")
    num_right_lanes: IntProperty(name="Right Lanes")
    traffic_light_direction: IntProperty(name="TL Direction")
    traffic_light_behaviour: IntProperty(name="TL Behaviour")
    is_train_crossing: IntProperty(name="Train Crossing")

class PathNodeData(PropertyGroup):
    name: StringProperty()
    x: FloatProperty(name="X", default=0.0)
    y: FloatProperty(name="Y", default=0.0)
    z: FloatProperty(name="Z", default=0.0)
    num_links: IntProperty(name="Number of Links", default=0)
    area_id: IntProperty(name="Area ID", default=0)
    node_id: IntProperty(name="Node ID", default=0)
    links: CollectionProperty(type=PathLink)
    car_links: CollectionProperty(type=PathCarLink)

# ----------------------------------------------------------------------------
#   Utility: clear existing data
# ----------------------------------------------------------------------------
def clear_pathnodes(context):
    sc = context.scene
    for obj in list(sc.collection.objects):
        if obj.get('is_pathnode'):
            bpy.data.objects.remove(obj, do_unlink=True)
    sc.pathnodes.clear()
    coll = bpy.data.collections.get("PathNodes")
    if coll:
        bpy.data.collections.remove(coll)

# ----------------------------------------------------------------------------
#   Import Operator
# ----------------------------------------------------------------------------
class IMPORT_OT_pathnodes(Operator, ImportHelper):
    bl_idname = "pathnodes.import_dat"
    bl_label = "Import .dat Files"
    filename_ext = ".dat"
    filter_glob: StringProperty(default="nodes*.dat", options={'HIDDEN'})
    files: CollectionProperty(type=PathNodeFileItem)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        sc = context.scene
        clear_pathnodes(context)
        main_coll = bpy.data.collections.new("PathNodes")
        sc.collection.children.link(main_coll)
        offset = 0
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            with open(filepath, 'rb') as f:
                total, numVeh, numPed, numCar, numLinks = struct.unpack('<IIIII', f.read(20))
                coords = []
                for i in range(total):
                    _, _, x, y, z, *_ = struct.unpack('<II3hHHHHBBI', f.read(28))
                    coords.append((x/8.0, y/8.0, z/8.0))
                raw_links = [struct.unpack('<II', f.read(8)) for _ in range(numLinks)]

            # create node empties and data
            for i, (x, y, z) in enumerate(coords):
                nd = sc.pathnodes.add()
                idx = offset + i
                nd.name = f"Node_{idx}"
                nd.x, nd.y, nd.z = x, y, z
                nd.node_id = i
                nd.num_links = 0
                obj = bpy.data.objects.new(nd.name, None)
                obj.empty_display_type = 'ARROWS'
                obj.empty_display_size = 0.2
                obj.location = Vector((x, y, z))
                obj['is_pathnode'] = True
                main_coll.objects.link(obj)

            # create links
            for a, b in raw_links:
                # skip invalid indices within this file range
                if a < 0 or b < 0 or a >= total or b >= total:
                    continue
                src = sc.pathnodes[a + offset]
                ln = src.links.add()
                ln.target_index = b + offset
                src.num_links += 1
                p1 = main_coll.objects.get(src.name)
                p2 = main_coll.objects.get(f"Node_{b+offset}")
                if p1 and p2:
                    ln.length = (p1.location - p2.location).length

            offset += total

        self.report({'INFO'}, f"Imported {len(self.files)} files, {offset} nodes.")
        return {'FINISHED'}

# ----------------------------------------------------------------------------
#   Export Operator
# ----------------------------------------------------------------------------
class EXPORT_OT_pathnodes(Operator, ExportHelper):
    bl_idname = "pathnodes.export_dat"
    bl_label = "Export .dat"
    
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        sc = context.scene
        total = len(sc.pathnodes)
        links = []
        for nd in sc.pathnodes:
            idx = int(nd.name.split('_')[-1])
            for ln in nd.links:
                links.append((idx, ln.target_index))

        with open(self.filepath, 'wb') as f:
            f.write(struct.pack('<IIIII', total, 0, 0, 0, len(links)))
            for nd in sc.pathnodes:
                x = int(nd.x * 8)
                y = int(nd.y * 8)
                z = int(nd.z * 8)
                f.write(struct.pack('<II3hHHHHBBI', 0, 0, x, y, z, 0, 0, 0, 0, 0, 0, 0))
            for a, b in links:
                f.write(struct.pack('<II', a, b))

        self.report({'INFO'}, f"Exported {total} nodes and {len(links)} links.")
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
        layout.operator(IMPORT_OT_pathnodes.bl_idname, icon='IMPORT')
        layout.operator(EXPORT_OT_pathnodes.bl_idname, icon='EXPORT')
        layout.separator()
        layout.template_list("UI_UL_list", "pathnodes_list", sc, "pathnodes", sc, "active_pathnode")
        if sc.pathnodes:
            nd = sc.pathnodes[sc.active_pathnode]
            col = layout.column()
            col.prop(nd, "x")
            col.prop(nd, "y")
            col.prop(nd, "z")
            col.prop(nd, "num_links")
            col.label(text="Links:")
            for ln in nd.links:
                col.label(text=f"→ {ln.target_index} ({ln.length:.2f})")

# ----------------------------------------------------------------------------
#   Registration
# ----------------------------------------------------------------------------
classes = [
    PathNodeFileItem,
    PathLink, PathCarLink, PathNodeData,
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