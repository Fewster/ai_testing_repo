import bpy
import math

# --------------------------------------------------------
# Properties
# --------------------------------------------------------
class RenderProps(bpy.types.PropertyGroup):
    base_name: bpy.props.StringProperty(
        name="Base Name",
        default="my_render"
    )
    step_angle: bpy.props.IntProperty(
        name="Rotation Step",
        default=45,
        min=1,
        max=360
    )
    output_path: bpy.props.StringProperty(
        name="Output Path",
        default="//",
        subtype="DIR_PATH"
    )

# --------------------------------------------------------
# Render Operator
# --------------------------------------------------------
class OBJECT_OT_render_rotations(bpy.types.Operator):
    bl_idname = "object.render_rotations"
    bl_label = "Render Rotations (Per Keyframe)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.render_props
        obj = context.active_object
        scene = context.scene

        if not obj:
            self.report({"ERROR"}, "No active object selected")
            return {"CANCELLED"}

        # Collect keyframes
        keyframes = set()
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    keyframes.add(int(kp.co[0]))

        if not keyframes:
            self.report({"ERROR"}, "No keyframes found")
            return {"CANCELLED"}

        counter = 1
        steps = int(360 / props.step_angle)

        for frame in sorted(keyframes):
            scene.frame_set(frame)

            for i in range(steps):
                obj.rotation_euler[2] = math.radians(i * props.step_angle)
                scene.render.filepath = f"{props.output_path}{props.base_name}_{counter}.png"
                bpy.ops.render.render(write_still=True)
                counter += 1

        return {"FINISHED"}

# --------------------------------------------------------
# Clean + Merge Operator
# --------------------------------------------------------
class OBJECT_OT_clean_and_merge(bpy.types.Operator):
    bl_idname = "object.clean_and_merge"
    bl_label = "Remove Empties & Merge Meshes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Remove empties
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                obj.select_set(True)
        bpy.ops.object.delete()

        # Merge selected meshes
        meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if len(meshes) > 1:
            context.view_layer.objects.active = meshes[0]
            bpy.ops.object.join()

        return {"FINISHED"}

# --------------------------------------------------------
# Create Root Operator
# --------------------------------------------------------
class OBJECT_OT_create_root(bpy.types.Operator):
    bl_idname = "object.create_root"
    bl_label = "Create Root Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected = context.selected_objects

        bpy.ops.object.empty_add(
            type='PLAIN_AXES',
            location=(0, 0, 0)
        )

        root = context.active_object
        root.name = "ROOT"

        # Parent selection to root
        for obj in selected:
            if obj != root:
                obj.parent = root

        return {"FINISHED"}

# --------------------------------------------------------
# UI Panel
# --------------------------------------------------------
class VIEW3D_PT_render_tools(bpy.types.Panel):
    bl_label = "Render Tools"
    bl_idname = "VIEW3D_PT_render_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RenderTools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.render_props

        layout.label(text="Render Settings")
        layout.prop(props, "base_name")
        layout.prop(props, "output_path")
        layout.prop(props, "step_angle")

        layout.separator()
        layout.operator("object.render_rotations", icon="RENDER_STILL")

        layout.separator()
        layout.label(text="Scene Utilities")
        layout.operator("object.create_root", icon="EMPTY_AXIS")
        layout.operator("object.clean_and_merge", icon="OUTLINER_OB_MESH")

# --------------------------------------------------------
# Registration
# --------------------------------------------------------
classes = (
    RenderProps,
    OBJECT_OT_render_rotations,
    OBJECT_OT_clean_and_merge,
    OBJECT_OT_create_root,
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
