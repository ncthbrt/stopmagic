import bpy
import re
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper
from pathlib import Path
import json
import tempfile
import subprocess
import os 
import time

class MeshSequenceAlembicExport(bpy.types.Operator, ExportHelper):
    bl_idname = "object.mesh_sequence_abc"       
    bl_label = "Export Alembic Sequence"
    bl_options = {'REGISTER'}   
    filename_ext = ".abc"
    
    should_loop: bpy.props.BoolProperty(
        name="Loop Action",
        description="Loop action.",
        default=True
    )

    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "should_loop")


    def execute(self, context):
        frame_end = -99999
        frame_start = 99999
        current_frame = bpy.context.scene.frame_current
        obs = list(bpy.context.selected_objects)

        objects = []
        
        framerate = 11 
        # Get length of the current action
        for o in obs:
            framerate = o.users_scene[0].render.fps
            this_end = o.users_scene[0].frame_end
            this_start = o.users_scene[0].frame_start
            if(this_end > frame_end): 
                frame_end = this_end
            if(this_start < frame_start): 
                frame_start = this_start

        temp_directory = Path(tempfile.gettempdir() + '/BlenderExportMeshSequence_'+ str(int(time.time()))).resolve()
        os.makedirs(str(temp_directory))
        file_path = Path(self.filepath)
        materials = {}
        
        bpy.ops.object.select_all(action='DESELECT')
            
        for o in obs:
            keyframes=[]
            o.select_set(True)
            object_material_slots={}        
            for i in range(frame_start, frame_end + 1): 
                bpy.context.scene.frame_current = i
                frame_materials=[]
                for mat in o.material_slots:
                    materials[mat.name] = True        
                    object_material_slots[mat.name] = True
                    frame_materials.append(mat.name)
                
                if len(frame_materials) > 0:
                    keyframes.append({"frame":i, "materials": list(frame_materials) })
                    filename = str(Path(str(temp_directory.resolve()) +"/" + re.sub(r'\.abc$',"_",file_path.name) + o.name + "_" + str(i) + ".obj").resolve())
                    bpy.ops.export_scene.obj(filepath=filename, use_materials=True, use_selection=True, use_blen_objects=True, group_by_object=True)

            
                
            o.select_set(False)
            
            if len(list(keyframes)) > 0:
                objects.append({
                    "name": o.name,
                    "keyframes": list(keyframes),
                    "materials": list(object_material_slots.keys())
                })        


        json_data_filename = str(Path(str(temp_directory.resolve()) +"/" + file_path.name + ".objseq").resolve())

    
        with open(json_data_filename, 'w') as outfile:
            json.dump({ 
                "materials": list(materials.keys()), 
                "frame_start": frame_start,
                "frame_end": frame_end,
                "frame_rate": framerate,
                "objects": list(objects),
                "loop": self.should_loop
            }, outfile)

        bpy.context.scene.frame_current = current_frame

        this_path = Path(os.path.dirname(os.path.realpath(__file__)))
        subprocess.run([str(Path(str(this_path.parent.resolve())+'/bin/StopMotionTool.exe')), '-f', json_data_filename, '-o',  str(file_path.absolute())], check=True, capture_output=True)
        os.rmdir(temp_directory)
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(MeshSequenceAlembicExport.bl_idname, text="Export Mesh Seq (.abc)")   

def register():
    bpy.utils.register_class(MeshSequenceAlembicExport)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
