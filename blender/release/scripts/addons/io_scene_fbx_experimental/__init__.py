# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "EXPERIMENTAL FBX format",
    "author": "Campbell Barton, Bastien Montagne, Jens Restemeier",
    "version": (3, 2, 0),
    "blender": (2, 72, 0),
    "location": "File > Import-Export",
    "description": "Experimental FBX io meshes, UV's, vertex colors, materials, "
                   "textures, cameras, lamps and actions",
    "warning": "Use at own risks! This addon is to test new fixes and features, *not* for every-day FBX io "
               "(unless you know what you are doing)",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/Autodesk_FBX",
    "category": "Import-Export",
}


if "bpy" in locals():
    import importlib
    if "import_fbx" in locals():
        importlib.reload(import_fbx)
    if "export_fbx_bin" in locals():
        importlib.reload(export_fbx_bin)
    if "export_fbx" in locals():
        importlib.reload(export_fbx)


import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       EnumProperty,
                       )

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )


class ImportFBX_experimental(bpy.types.Operator, ImportHelper):
    """Load a FBX geometry file"""
    bl_idname = "import_scene.fbx_experimental"
    bl_label = "Import FBX - Experimental"
    bl_options = {'UNDO', 'PRESET'}

    directory = StringProperty()

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    use_manual_orientation = BoolProperty(
            name="Manual Orientation",
            description="Specify orientation and scale, instead of using embedded data in FBX file",
            default=False,
            )
    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='-Z',
            )
    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
            )
    global_scale = FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=1.0,
            )
    bake_space_transform = BoolProperty(
            name="Apply Transform",
            description=("Bake space transform into object data, avoids getting unwanted rotations to objects when "
                         "target space is not aligned with Blender's space "
                         "(WARNING! experimental option, might give odd/wrong results)"),
            default=False,
            )

    use_image_search = BoolProperty(
            name="Image Search",
            description="Search subdirs for any associated images (Warning, may be slow)",
            default=True,
            )

    use_alpha_decals = BoolProperty(
            name="Alpha Decals",
            description="Treat materials with alpha as decals (no shadow casting)",
            default=False,
            options={'HIDDEN'}
            )
    decal_offset = FloatProperty(
            name="Decal Offset",
            description="Displace geometry of alpha meshes",
            min=0.0, max=1.0,
            default=0.0,
            options={'HIDDEN'}
            )

    use_custom_props = BoolProperty(
            name="Import user properties",
            description="Import user properties as custom properties",
            default=True,
            options={'HIDDEN'},
            )
    use_custom_props_enum_as_string = BoolProperty(
            name="Import enum properties as string",
            description="Store enumeration values as string",
            default=True,
            options={'HIDDEN'},
            )

    ignore_leaf_bones = BoolProperty(
            name="Ignore leaf bones",
            description="Ignore the last bone at the end of a chain that is used to mark the length of the previous bone",
            default=False,
            options={'HIDDEN'},
            )

    automatic_bone_orientation = BoolProperty(
            name="Automatic Bone Orientation",
            description="Try to align the major bone axis with the bone children",
            default=False,
            options={'HIDDEN'},
            )
    primary_bone_axis = EnumProperty(
            name="Primary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='Y',
            )
    secondary_bone_axis = EnumProperty(
            name="Secondary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='X',
            )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "use_manual_orientation"),
        sub = layout.column()
        sub.enabled = self.use_manual_orientation
        sub.prop(self, "axis_forward")
        sub.prop(self, "axis_up")
        sub.prop(self, "global_scale")
        layout.prop(self, "bake_space_transform")

        layout.prop(self, "use_image_search")
        # layout.prop(self, "use_alpha_decals")
        layout.prop(self, "decal_offset")

        layout.prop(self, "use_custom_props")
        sub = layout.row()
        sub.enabled = self.use_custom_props
        sub.prop(self, "use_custom_props_enum_as_string")

        layout.prop(self, "ignore_leaf_bones")

        layout.prop(self, "automatic_bone_orientation"),
        sub = layout.column()
        sub.enabled = not self.automatic_bone_orientation
        sub.prop(self, "primary_bone_axis")
        sub.prop(self, "secondary_bone_axis")

    def execute(self, context):
        print("Using EXPERIMENTAL FBX export!")
        keywords = self.as_keywords(ignore=("filter_glob", "directory"))
        keywords["use_cycles"] = (context.scene.render.engine == 'CYCLES')

        from . import import_fbx
        return import_fbx.load(self, context, **keywords)


class ExportFBX_experimental(bpy.types.Operator, ExportHelper):
    """Selection to an ASCII Autodesk FBX"""
    bl_idname = "export_scene.fbx_experimental"
    bl_label = "Export FBX - Experimental"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection = BoolProperty(
            name="Selected Objects",
            description="Export selected objects on visible layers",
            default=False,
            )
    global_scale = FloatProperty(
            name="Scale",
            description="Scale all data (Some importers do not support scaled armatures!)",
            min=0.001, max=1000.0,
            soft_min=0.01, soft_max=1000.0,
            default=1.0,
            )
    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='-Z',
            )
    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
            )
    bake_space_transform = BoolProperty(
            name="Apply Transform",
            description=("Bake space transform into object data, avoids getting unwanted rotations to objects when "
                         "target space is not aligned with Blender's space "
                         "(WARNING! experimental option, might give odd/wrong results)"),
            default=False,
            )

    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LAMP', "Lamp", ""),
                   ('ARMATURE', "Armature", ""),
                   ('MESH', "Mesh", ""),
                   ('OTHER', "Other", "Other geometry types, like curve, metaball, etc. (converted to meshes)"),
                   ),
            description="Which kind of object to export",
            default={'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH', 'OTHER'},
            )

    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers to mesh objects (except Armature ones!)",
            default=True,
            )
    mesh_smooth_type = EnumProperty(
            name="Smoothing",
            items=(('OFF', "Off", "Don't write smoothing, export normals instead"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            description=("Export smoothing information "
                         "(prefer 'Off' option if your target importer understand split normals)"),
            default='OFF',
            )
    use_mesh_edges = BoolProperty(
            name="Loose Edges",
            description="Export loose edges (as two-vertices polygons)",
            default=False,
            )
    use_tspace = BoolProperty(
            name="Tangent Space",
            description=("Add binormal and tangent vectors, together with normal they form the tangent space "
                         "(will only work correctly with tris/quads only meshes!)"),
            default=False,
            )
    use_custom_props = BoolProperty(
            name="Custom Properties",
            description="Export custom properties",
            default=False,
            )
    add_leaf_bones = BoolProperty(
            name="Add leaf bones",
            description=("Append a last bone to the end of each chain to specify bone length. It is useful to, "
                         "enable this when exporting into another modelling application and to disable this when"
                         "exporting into a game engine or real-time viewer."),
            default=True # False for commit!
            )
    primary_bone_axis = EnumProperty(
            name="Primary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='Y',
            )
    secondary_bone_axis = EnumProperty(
            name="Secondary Bone Axis",
            items=(('X', "X Axis", ""),
                   ('Y', "Y Axis", ""),
                   ('Z', "Z Axis", ""),
                   ('-X', "-X Axis", ""),
                   ('-Y', "-Y Axis", ""),
                   ('-Z', "-Z Axis", ""),
                   ),
            default='X',
            )
    use_armature_deform_only = BoolProperty(
            name="Only Deform Bones",
            description="Only write deforming bones (and non-deforming ones when they have deforming children)",
            default=False,
            )
    # Anim
    bake_anim = BoolProperty(
            name="Baked Animation",
            description="Export baked keyframe animation",
            default=True,
            )
    bake_anim_use_nla_strips = BoolProperty(
            name="NLA Strips",
            description=("Export each non-muted NLA strip as a separated FBX's AnimStack, if any, "
                         "instead of global scene animation"),
            default=True,
            )
    bake_anim_use_all_actions = BoolProperty(
            name="All Actions",
            description=("Export each action as a separated FBX's AnimStack, "
                         "instead of global scene animation"),
            default=True,
            )
    bake_anim_step = FloatProperty(
            name="Sampling Rate",
            description=("How often to evaluate animated values (in frames)"),
            min=0.01, max=100.0,
            soft_min=0.1, soft_max=10.0,
            default=1.0,
            )
    bake_anim_simplify_factor = FloatProperty(
            name="Simplify",
            description=("How much to simplify baked values (0.0 to disable, the higher the more simplified"),
            min=0.0, max=10.0,  # No simplification to up to 0.05 slope/100 max_frame_step.
            default=1.0,  # default: min slope: 0.005, max frame step: 10.
            )
    path_mode = path_reference_mode
    embed_textures = BoolProperty(
            name="Embed Textures",
            description="Embed textures in FBX binary file (only for \"Copy\" path mode!)",
            default=False,
            )
    batch_mode = EnumProperty(
            name="Batch Mode",
            items=(('OFF', "Off", "Active scene to file"),
                   ('SCENE', "Scene", "Each scene as a file"),
                   ('GROUP', "Group", "Each group as a file"),
                   ),
            )
    use_batch_own_dir = BoolProperty(
            name="Batch Own Dir",
            description="Create a dir for each exported file",
            default=True,
            )
    use_metadata = BoolProperty(
            name="Use Metadata",
            default=True,
            options={'HIDDEN'},
            )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "use_selection")
        layout.prop(self, "global_scale")
        layout.prop(self, "axis_forward")
        layout.prop(self, "axis_up")
        layout.prop(self, "bake_space_transform")

        layout.separator()
        layout.prop(self, "object_types")
        layout.prop(self, "use_mesh_modifiers")
        layout.prop(self, "mesh_smooth_type")
        layout.prop(self, "use_mesh_edges")
        sub = layout.row()
        sub.enabled = self.mesh_smooth_type in {'OFF'}
        sub.prop(self, "use_tspace")
        layout.prop(self, "use_armature_deform_only")
        layout.prop(self, "use_custom_props")
        layout.prop(self, "add_leaf_bones")
        layout.prop(self, "primary_bone_axis")
        layout.prop(self, "secondary_bone_axis")
        layout.prop(self, "bake_anim")
        col = layout.column()
        col.enabled = self.bake_anim
        col.prop(self, "bake_anim_use_nla_strips")
        col.prop(self, "bake_anim_use_all_actions")
        col.prop(self, "bake_anim_step")
        col.prop(self, "bake_anim_simplify_factor")

        layout.separator()
        layout.prop(self, "path_mode")
        col = layout.column()
        col.enabled = (self.path_mode == 'COPY')
        col.prop(self, "embed_textures")
        layout.prop(self, "batch_mode")
        layout.prop(self, "use_batch_own_dir")

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from mathutils import Matrix
        from . import export_fbx_bin
        print("Using EXPERIMENTAL FBX import!")
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = (Matrix.Scale(self.global_scale, 4) *
                         axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())

        keywords = self.as_keywords(ignore=("global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            ))

        keywords["global_matrix"] = global_matrix

        return export_fbx_bin.save(self, context, **keywords)


def menu_func_import(self, context):
    self.layout.operator(ImportFBX_experimental.bl_idname, text="Experimental FBX (.fbx)")


def menu_func_export(self, context):
    self.layout.operator(ExportFBX_experimental.bl_idname, text="Experimental FBX (.fbx)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
