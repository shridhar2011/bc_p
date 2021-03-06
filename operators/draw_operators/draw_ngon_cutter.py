import bpy
import bgl
import blf
import bpy_extras.view3d_utils
from mathutils import Vector
import bmesh
from bpy.props import *
from ... utils.objects import set_active
from ... utils.modifiers import apply_modifiers, create_solidify_modifier
from ... graphic.draw_px import draw_extending_ngon
from . draw_utils import set_evet_region, append_vert_to_list, set_saved_region, check_if_moving, boxcutter_show_wire, generate_3d_mesh, set_grid_path, saved_cords
from ... ui.main_panel import boxcutter_enable_hops

class BoxCutterDrawNgon(bpy.types.Operator):
        """Draw an ngon with the mouse"""
        bl_idname = "boxcutter.draw_ngon"
        bl_label = "Box Cutter Draw Ngon"
        bl_options = {'REGISTER', 'UNDO'}
        
        cut_mode = BoolProperty(name = "Cut Mode",
                              description = "cut mode",
                              default = True)

        def execute(self, context):


            boxcutter_show_wire(self, context, False)
            generate_3d_mesh(self, context, 'NGON')
            
            if self.first_active in list(bpy.context.selected_objects):
                bpy.context.scene.objects.active = self.first_active
                bpy.ops.boxcutter.bool_difference()
                set_active(self.first_active, True)
                if boxcutter_enable_hops():
                    object = bpy.context.active_object
                    if object.hops.status in ("CSHARP", "SUBSHARP"):
                        bpy.ops.hops.soft_sharpen()

                    if object.hops.status == "UNDEFINED":
                        bpy.ops.hops.complex_sharpen()

                    if object.hops.status == "CSTEP":
                        if bpy.context.scene.BoxCutter_bool_method == 'BMESH':
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.hide(unselected=True)
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.mesh.edges_select_sharp(sharpness=0.523599)
                            bpy.ops.transform.edge_bevelweight(value=1)
                            bpy.ops.mesh.mark_sharp()
                            bpy.ops.object.editmode_toggle()
                        else:
                            bpy.ops.step.sstep()


            else:
                pass

            bpy.context.scene.BoxCutter_shape_moving = False


            return {'FINISHED'}

        def modal(self, context, event):
            context.area.tag_redraw()

            if event.type == 'MOUSEMOVE':
                grid_path_x, grid_path_y = set_grid_path(self,context, event)
                self.mouse_path = Vector((grid_path_x, grid_path_y))

            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS' and ( event.ctrl or event.shift ) and not event.alt :

                add_cursor_point_to_list(self, context, event)

                return {'RUNNING_MODAL'}

            elif event.type == 'RIGHTMOUSE' :
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'CANCELLED'}


            elif event.type == 'LEFTMOUSE'  and not event.shift and not event.alt and not event.ctrl and len(self.list_location_3d) >= 2:

                add_cursor_point_to_list(self, context, event)

                self.use_3d_cursor = False
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.execute(context)

                return {'FINISHED'}

            elif event.alt and event.type == 'LEFTMOUSE'  and (len(self.list_location_3d) >= 2 ):

                add_cursor_point_to_list(self, context, event)
                
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.execute(context)

                return {'FINISHED'}

            elif event.type == 'MIDDLEMOUSE'  and (len(self.list_location_3d) >= 2 ):

                add_cursor_point_to_list(self, context, event)
                
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.execute(context)

                return {'FINISHED'}


            elif event.type in {'ESC'}:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.depth_location = Vector((0.0, 0.0, 0.0))
                return {'FINISHED'}


            if event.type == 'SPACE' and event.value == 'PRESS':
                self.savedx = -(self.mouse_path[0] - self.first_mouse_x)
                self.savedy = -(self.mouse_path[1] - self.first_mouse_y)
                
                if bpy.context.scene.BoxCutter_shape_moving == False:
                    bpy.context.scene.BoxCutter_shape_moving = True
                elif bpy.context.scene.BoxCutter_shape_moving == True:
                    bpy.context.scene.BoxCutter_shape_moving = False

            return {'RUNNING_MODAL'}

        def invoke(self, context, event):
            self.use_3d_cursor = True
            if context.area.type == 'VIEW_3D':
                self.first_active = bpy.context.scene.objects.active
                args = (self, context)
                boxcutter_show_wire(self, context, True)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_extending_ngon, args, 'WINDOW', 'POST_PIXEL')

                grid_path_x, grid_path_y = set_grid_path(self,context, event)
                self.mouse_path = Vector((grid_path_x, grid_path_y))

                self.list_location_3d = []
                set_evet_region(self, event, True)
                append_vert_to_list(self, context, grid_path_x, grid_path_y)
                context.window_manager.modal_handler_add(self)

                return {'RUNNING_MODAL'}
            else:
                return {'CANCELLED'}

def add_cursor_point_to_list(self, context, event):

    region = context.region
    rv3d = context.space_data.region_3d

    self.depth_location = bpy.context.scene.cursor_location
    mouse_loc_2d = self.mouse_path
    mouse_loc_3d = bpy_extras.view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_loc_2d, self.depth_location)
    self.list_location_3d.append(mouse_loc_3d)
    self.depth_location = self.list_location_3d[-1]
