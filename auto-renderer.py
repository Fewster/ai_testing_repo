import bpy
import math

# --------------------------------------------------------
# Properties (stored on Scene)
# --------------------------------------------------------
class RenderProps(bpy.types.PropertyGroup):
    base_name: bpy.props.StringProperty(
        name="Base Name",
        description="Base name for rendered images",
        default="my_render"
    )
    step_angle: bpy.props.IntProperty(
        name="Rotation Step",
        description="Rotation step in degrees",
        default=45,
        min=1,
        max=360
    )
    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="Path to save renders (// = relative to blend file)",
        default="//",
        subtype="DIR_PATH"
    )

# --------------------------------------------------------
# Operator: Render Rotations for Each Keyframe
# --------------------------------------------------------
class OBJECT_OT_render_rotations(bpy.types.Operator):
    bl_idname = "object.render_rotations"
    bl_label = "Render Rotations (per Keyframe)"
    bl_description = "Rotate object in increments for each keyframe and render"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.render_props
        base_name = props.base_name
        output_path = props.output_path
        step_angle = props.step_angle

        obj = context.active_object
        scene = context.scene

        if obj is None:
            self.report({"ERROR"}, "No active object selected.")
            return {"CANCELLED"}

        # Collect keyframes
        keyframes = set()
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    keyframes.add(int(kp.co[0]))
        keyframes = sorted(list(keyframes))

        if not keyframes:
            self.report({"ERROR"}, "No keyframes found for active object.")
            return {"CANCELLED"}

        counter = 1
        steps = int(360 / step_angle)

        for frame in keyframes:
            scene.frame_set(frame)

            for i in range(steps):
                obj.rotation_euler[2] = math.radians(i * step_angle)

                filepath = f"{output_path}{base_name}_{counter}.png"
                scene.render.filepath = filepath

                bpy.ops.render.render(write_still=True)
                self.report({"INFO"}, f"Rendered: {filepath}")
                counter += 1

        self.report({"INFO"}, "All renders complete!")
        return {"FINISHED"}

# --------------------------------------------------------
# Operator: Remove Empties and Merge Meshes
# --------------------------------------------------------
class OBJECT_OT_clean_and_merge(bpy.types.Operator):
    bl_idname = "object.clean_and_merge"
    bl_label = "Remove Empties & Merge Meshes"
    bl_description = "Deletes all empty nodes and merges selected meshes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Delete all empties
        empties = [obj for obj in bpy.data.objects if obj.type == 'EMPTY']
        bpy.ops.object.select_all(action='DESELECT')
        for empty in empties:
            empty.select_set(True)
        if empties:
            bpy.ops.object.delete()

        # Merge selected meshes
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if len(selected_meshes) > 1:
            bpy.context.view_layer.objects.active = selected_meshes[0]
            for obj in selected_meshes:
                obj.select_set(True)
            bpy.ops.object.join()

        return {"FINISHED"}

# --------------------------------------------------------
# Panel UI
# --------------------------------------------------------
class VIEW3D_PT_render_tools(bpy.types.Panel):
    bl_label = "Custom Render Tools"
    bl_idname = "VIEW3D_PT_render_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RenderTools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.render_props

        layout.prop(props, "base_name")
        layout.prop(props, "output_path")
        layout.prop(props, "step_angle")

        layout.separator()
        layout.operator("object.render_rotations", icon="RENDER_STILL")
        layout.separator()
        layout.operator("object.clean_and_merge", icon="MESH_CUBE")

# --------------------------------------------------------
# Registration
# --------------------------------------------------------
classes = (
    RenderProps,
    OBJECT_OT_render_rotations,
    OBJECT_OT_clean_and_merge,
    VIEW3D_PT_render_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_props = bpy.props.PointerProperty(type=RenderProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.render_props

if __name__ == "__main__":
    register()
