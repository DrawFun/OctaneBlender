### BEGIN GPL LICENSE BLOCK #####
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

import bpy, os
from bpy.types import Operator, Panel
from bpy.props import *

from object_physics_meadow import meadow, settings as _settings, patch, blob, physics
from object_physics_meadow.settings import find_meadow_object
from object_physics_meadow.util import *
from object_physics_meadow import progress

# default progress reports
def progress_default():
    progress.show_progress_bar = True
    progress.show_stdout = True

class OBJECT_PT_Meadow(Panel):
    """Settings for meadow components"""
    bl_label = "Meadow"
    bl_idname = "OBJECT_PT_meadow"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob:
            return False
        return True
    
    def draw(self, context):
        settings = _settings.get(context)
        groundob = find_meadow_object(context, 'GROUND')
        has_samples = blob.object_has_blob_data(groundob) if groundob else False
        ob = context.object
        meadow = ob.meadow
        layout = self.layout
        
        layout.prop(meadow, "type", expand=True)
        
        layout.separator()
        
        if meadow.type == 'TEMPLATE':
            row = layout.row()
            if groundob:
                row.prop_search(meadow, "density_vgroup_name", groundob, "vertex_groups", text="Density Vertex Group")
            else:
                row.active = False
                row.prop(meadow, "density_vgroup_name", text="Density Vertex Group")
            
            row = layout.row()
            row.prop(meadow, "use_as_dupli")
            sub = row.row()
            sub.enabled = meadow.use_as_dupli
            sub.prop(meadow, "use_centered")
            row = layout.row()
            row.prop(meadow, "hide")
        
        elif meadow.type == 'GROUND':
            box = layout.box()
            
            sub = box.column()
            # this politely prevents users from changing settings unwantedly,
            # they have to delete the samples first
            sub.enabled = not has_samples
            sub.prop(meadow, "seed")
            col = sub.column(align=True)
            col.prop(meadow, "sample_distance")
            sub2 = col.row(align=True)
            sub2.prop(meadow, "max_samples")
            sub2.operator("meadow.estimate_max_samples", text="Estimate")
            sub.prop(meadow, "sampling_levels")
            
            if has_samples:
                box.operator("meadow.delete_blobs", icon='X', text="Delete Samples")
            else:
                box.operator("meadow.make_blobs", icon='STICKY_UVS_DISABLE', text="Create Samples")
        
        layout.separator()
        
        col = layout.column()
        col.enabled = has_samples

        box = col.box()
        box.prop(meadow, "slope_rotation")
        box.operator("meadow.make_patches", icon='PARTICLE_PATH', text="Update Patches")
        
        row = col.row()
        row.operator("meadow.bake_physics", icon='MOD_PHYSICS')
        row.operator("meadow.free_physics", icon='X')

        if groundob:
            row = layout.row()
            row.prop(groundob.meadow, "use_layers")
            sub = row.row()
            if groundob.meadow.use_layers:
                sub.template_layers(groundob.meadow, "layers", groundob.meadow, "used_layers", -1)
            else:
                sub.enabled = False
                sub.template_layers(groundob, "layers", groundob.meadow, "used_layers", -1)


class MeadowOperatorBase():
    def verify_cache_dir(self):
        if not bpy.data.is_saved:
            self.report({'ERROR'}, "File must be saved for generating external cache directory")
            return False, ""
        
        cache_dir = bpy.path.abspath("//meadow_cache")
        if os.path.exists(cache_dir):
            if not os.path.isdir(cache_dir):
                self.report({'ERROR'}, "%s is not a directory" % cache_dir)
                return False, ""
        else:
            try:
                os.mkdir(cache_dir)
            except OSError as err:
                self.report({'ERROR'}, "{0}".format(err))
                return False, ""
        return True, cache_dir


class EstimateMaxSamplesOperator(MeadowOperatorBase, Operator):
    """Estimate an upper bound for the number of samples fitting on the ground object"""
    bl_idname = "meadow.estimate_max_samples"
    bl_label = "Estimate Maximum Samples"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        groundob = find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        
        meadow.estimate_max_samples(context, groundob)
        
        return {'FINISHED'}


class MakeBlobsOperator(MeadowOperatorBase, Operator):
    """Generate Blob objects storing dupli distribution"""
    bl_idname = "meadow.make_blobs"
    bl_label = "Make Blobs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        #cache_ok, cache_dir = self.verify_cache_dir()
        #if not cache_ok:
        #    return {'CANCELLED'}
        if not settings.blob_group(context):
            bpy.data.groups.new(settings.blob_groupname)
        
        groundob = find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        blobgridob = find_meadow_object(context, 'BLOBGRID')
        if not blobgridob:
            self.report({'ERROR'}, "Could not find meadow Blob Grid object")
            return {'CANCELLED'}
        
        with ObjectSelection():
            progress_default()
            meadow.make_blobs(context, blobgridob, groundob)
        
        return {'FINISHED'}


class DeleteBlobsOperator(MeadowOperatorBase, Operator):
    """Delete Blob objects storing dupli distribution"""
    bl_idname = "meadow.delete_blobs"
    bl_label = "Delete Blobs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        groundob = find_meadow_object(context, 'GROUND')
        
        with ObjectSelection():
            progress_default()
            meadow.delete_blobs(context, groundob)
        
        return {'FINISHED'}


class MakePatchesOperator(MeadowOperatorBase, Operator):
    """Make Patch copies across the grid for simulation and set up duplis"""
    bl_idname = "meadow.make_patches"
    bl_label = "Make Patches"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        settings = _settings.get(context)
        
        if not settings.patch_group(context):
            bpy.data.groups.new(settings.patch_groupname)
        if not settings.blob_group(context):
            bpy.data.groups.new(settings.blob_groupname)
        
        groundob = find_meadow_object(context, 'GROUND')
        if not groundob:
            self.report({'ERROR'}, "Could not find meadow Ground object")
            return {'CANCELLED'}
        blobgridob = find_meadow_object(context, 'BLOBGRID')
        if not blobgridob:
            self.report({'ERROR'}, "Could not find meadow Blob Grid object")
            return {'CANCELLED'}
        
        with ObjectSelection():
            progress_default()
            meadow.make_patches(context, blobgridob, groundob)
        
        return {'FINISHED'}


# Combines blob + patches operator for menu entry
class MakeMeadowOperator(MeadowOperatorBase, Operator):
    """Make blobs and patches based on designated meadow objects"""
    bl_idname = "meadow.make_meadow"
    bl_label = "Make Meadow"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        result = bpy.ops.meadow.make_blobs()
        if 'FINISHED' not in result:
            return result
        result = bpy.ops.meadow.make_patches()
        if 'FINISHED' not in result:
            return result
        
        return {'FINISHED'}


class MEADOW_OT_BakePhysics(MeadowOperatorBase, Operator):
    """Bake all physics caches"""
    bl_idname = "meadow.bake_physics"
    bl_label = "Bake Physics"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        with ObjectSelection():
            progress_default()
            physics.scene_bake_all(context)
        return {'FINISHED'}


class MEADOW_OT_FreePhysics(MeadowOperatorBase, Operator):
    """Free all physics caches"""
    bl_idname = "meadow.free_physics"
    bl_label = "Free Physics"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        with ObjectSelection():
            progress_default()
            physics.scene_free_all(context)
        return {'FINISHED'}


def menu_generate_meadow(self, context):
    self.layout.operator("meadow.make_meadow", icon='PARTICLE_PATH')

def register():
    bpy.utils.register_class(OBJECT_PT_Meadow)
    
    bpy.utils.register_class(EstimateMaxSamplesOperator)
    bpy.utils.register_class(MakeBlobsOperator)
    bpy.utils.register_class(DeleteBlobsOperator)
    bpy.utils.register_class(MakePatchesOperator)
    bpy.utils.register_class(MakeMeadowOperator)
    bpy.utils.register_class(MEADOW_OT_BakePhysics)
    bpy.utils.register_class(MEADOW_OT_FreePhysics)
    bpy.types.INFO_MT_add.append(menu_generate_meadow)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_Meadow)
    
    bpy.utils.unregister_class(EstimateMaxSamplesOperator)
    bpy.types.INFO_MT_add.remove(menu_generate_meadow)
    bpy.utils.unregister_class(MakeBlobsOperator)
    bpy.utils.unregister_class(DeleteBlobsOperator)
    bpy.utils.unregister_class(MakePatchesOperator)
    bpy.utils.unregister_class(MakeMeadowOperator)
    bpy.utils.unregister_class(MEADOW_OT_BakePhysics)
    bpy.utils.unregister_class(MEADOW_OT_FreePhysics)
