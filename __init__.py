import bpy

bl_info = {
    "name": "快速设置相机",
    "author": "一枫",
    "version": (15, 5),
    "blender": (3, 0, 0),
    "location": "Object Mode > E / 3D View > N 面板 > 快速设置相机",
    "description": "相机专用快速设置工具（快捷键 D 弹窗）",
    "category": "Object",
}

# =========================
# 预设常量
# =========================

FOCAL_LENGTH_PRESETS = [12, 18, 24, 35, 50, 85, 135, 200]
FSTOP_PRESETS = [1.2, 1.4, 1.8, 2.0, 2.8, 4.0, 5.6, 8.0, 11, 16, 22]

MODULE_TITLE_COMPOSITION = "构图辅助"
MODULE_TITLE_LENS = "镜头设置"
MODULE_TITLE_PASSEPARTOUT = "取景与背景"
MODULE_TITLE_DOF = "景深设置"

addon_keymaps = []


# =========================
# 工具函数
# =========================

def get_addon_prefs():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def get_module_visibility(context):
    scene = getattr(context, "scene", None)
    return getattr(scene, "quickcam_module_visibility", None) if scene else None


def module_is_enabled(context, prop_name):
    settings = get_module_visibility(context)
    return bool(getattr(settings, prop_name, True)) if settings else True


def ui_prop(layout, data, prop, text=None, factor=0.35, toggle=False, icon='NONE'):
    kwargs = {"text": "", "toggle": toggle}
    if icon != 'NONE':
        kwargs["icon"] = icon

    if not text:
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.prop(data, prop, **kwargs)
        return

    row = layout.row(align=True)
    row.scale_y = 1.2
    split = row.split(factor=factor, align=True)
    col_label = split.column(align=True)
    col_label.alignment = 'LEFT'
    col_label.label(text=text)
    col_prop = split.column(align=True)
    col_prop.prop(data, prop, **kwargs)


# =========================
# 插件偏好
# =========================

class QUICKCAM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    popup_width: bpy.props.IntProperty(
        name="相机弹窗宽度",
        default=240,
        min=180,
        max=500,
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="弹窗设置")
        col.prop(self, "popup_width")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="默认快捷键：D = 相机快速设置")
        col.label(text="N 面板入口：3D 视图 > N 面板 > 快速设置相机")


# =========================
# N 面板模块显示设置
# =========================

class QUICKCAM_ModuleVisibility(bpy.types.PropertyGroup):
    show_composition: bpy.props.BoolProperty(
        name=MODULE_TITLE_COMPOSITION,
        description="显示九宫格、中心点等构图辅助线设置",
        default=True,
    )
    show_lens: bpy.props.BoolProperty(
        name=MODULE_TITLE_LENS,
        description="显示焦距、预设和相机类型设置",
        default=True,
    )
    show_passepartout: bpy.props.BoolProperty(
        name=MODULE_TITLE_PASSEPARTOUT,
        description="显示外框与背景图设置",
        default=True,
    )
    show_dof: bpy.props.BoolProperty(
        name=MODULE_TITLE_DOF,
        description="显示景深相关设置",
        default=True,
    )


# =========================
# Operators（相机专用）
# =========================

class CAMERA_OT_set_focal_length(bpy.types.Operator):
    bl_idname = "camera.set_focal_length"
    bl_label = "设置焦距"
    bl_options = {'UNDO'}

    focal_length: bpy.props.FloatProperty(default=50.0)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        context.active_object.data.lens = self.focal_length
        return {'FINISHED'}


class CAMERA_OT_set_fstop(bpy.types.Operator):
    bl_idname = "camera.set_fstop"
    bl_label = "设置光圈"
    bl_options = {'UNDO'}

    fstop: bpy.props.FloatProperty(default=2.8)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        context.active_object.data.dof.aperture_fstop = self.fstop
        return {'FINISHED'}


class CAMERA_OT_enable_passepartout(bpy.types.Operator):
    bl_idname = "camera.enable_passepartout"
    bl_label = "开启外框"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        context.active_object.data.show_passepartout = True
        return {'FINISHED'}


# =========================
# UI 绘制（无任何窗口标题和多余文字标签）
# =========================

def draw_module_visibility_controls(layout, context):
    settings = get_module_visibility(context)
    if not settings:
        return

    box = layout.box()
    row = box.row(align=True)
    row.label(text="模块显示", icon='CHECKBOX_HLT')
    for prop in ("show_composition", "show_lens", "show_passepartout", "show_dof"):
        enabled = bool(getattr(settings, prop, True))
        row.prop(settings, prop, text="", icon='RESTRICT_VIEW_OFF' if enabled else 'RESTRICT_VIEW_ON', icon_only=True, emboss=False)


def draw_module_box(layout, title, icon):
    box = layout.box()
    row = box.row(align=True)
    row.label(text=title, icon=icon)
    return box


def draw_camera_ui(layout, context, obj, show_view_controls=False):
    cam = obj.data

    if show_view_controls:
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("camera.align_to_view", text="对齐视图", icon='CAMERA_DATA')
        row.operator("camera.view_from_camera", text="相机视图", icon='RESTRICT_VIEW_OFF')

    # 1. 构图辅助
    box = draw_module_box(layout, MODULE_TITLE_COMPOSITION, 'MESH_GRID')
    if module_is_enabled(context, "show_composition"):
        if any(hasattr(cam, attr) for attr in ["show_composition_thirds", "show_composition_center", "show_composition_golden"]):
            col = box.column(align=True)
            row = col.row(align=True)
            row.scale_y = 1.2
            for prop, txt in [("show_composition_thirds", "九宫"), ("show_composition_center", "中心"), ("show_composition_golden", "黄金")]:
                if hasattr(cam, prop):
                    row.prop(cam, prop, text=txt, toggle=True)

    # 2. 镜头
    box = draw_module_box(layout, MODULE_TITLE_LENS, 'CAMERA_DATA')
    if module_is_enabled(context, "show_lens"):
        col = box.column(align=True)

        ui_prop(col, cam, "lens", text="焦距", factor=0.35)

        flow = col.grid_flow(row_major=True, columns=4, even_columns=True, align=True)
        flow.scale_y = 1.2
        current_lens = getattr(cam, "lens", None)
        for f in FOCAL_LENGTH_PRESETS:
            is_active = (
                current_lens is not None
                and abs(float(current_lens) - float(f)) <= 0.01
            )
            op = flow.operator("camera.set_focal_length", text=str(f), depress=is_active)
            op.focal_length = f

        row = col.row(align=True)
        row.scale_y = 1.2
        split = row.split(factor=0.35, align=True)
        split.label(text="类型")
        split.prop(cam, "type", text="")

        if cam.type == 'ORTHO':
            ui_prop(col, cam, "ortho_scale", text="视野", factor=0.35)

    # 3. 取景与背景
    box = draw_module_box(layout, MODULE_TITLE_PASSEPARTOUT, 'IMAGE_DATA')
    if module_is_enabled(context, "show_passepartout"):
        col = box.column(align=True)

        row = col.row(align=True)
        row.scale_y = 1.2
        row.prop(cam, "show_passepartout", text="外框开关", toggle=True)

        if cam.show_passepartout:
            ui_prop(col, cam, "passepartout_alpha", text="外框透明度", factor=0.35)

        ui_prop(col, cam, "show_background_images", text="背景图", toggle=False, factor=0.35)

        if cam.show_background_images and cam.background_images:
            for i, bg in enumerate(cam.background_images):
                name = bg.image.name if bg.image else f"图层 {i+1}"
                ui_prop(col, bg, "alpha", text=name, factor=0.35)

    # 4. 景深
    box = draw_module_box(layout, MODULE_TITLE_DOF, 'RESTRICT_SELECT_OFF')
    if module_is_enabled(context, "show_dof"):
        row = box.row(align=True)
        row.scale_y = 1.2
        row.prop(cam.dof, "use_dof", text="启用景深", icon='CHECKBOX_HLT' if cam.dof.use_dof else 'CHECKBOX_DEHLT', toggle=True)

        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("camera.focus_selected", text="聚焦选中物体", icon='RESTRICT_SELECT_OFF')

        if cam.dof.use_dof:
            col = box.column(align=True)
            ui_prop(col, cam.dof, "focus_object", text="焦点", factor=0.35)
            if not cam.dof.focus_object:
                ui_prop(col, cam.dof, "focus_distance", text="距离", factor=0.35)

            ui_prop(col, cam.dof, "aperture_fstop", text="光圈", factor=0.35)

            flow = col.grid_flow(row_major=True, columns=4, even_columns=True, align=True)
            flow.scale_y = 1.2
            current_fstop = getattr(cam.dof, "aperture_fstop", None)
            for f in FSTOP_PRESETS:
                txt = f"{f:.1f}" if f % 1 != 0 else str(int(f))
                is_active = (
                    current_fstop is not None
                    and abs(float(current_fstop) - float(f)) <= 0.01
                )
                op = flow.operator("camera.set_fstop", text=txt, depress=is_active)
                op.fstop = f


# =========================
# N 面板
# =========================

class VIEW3D_PT_quick_settings_camera(bpy.types.Panel):
    bl_label = "快速设置相机"
    bl_idname = "VIEW3D_PT_quick_settings_camera"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "快速设置相机"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        draw_module_visibility_controls(layout, context)

        if not obj or obj.type != 'CAMERA':
            box = layout.box()
            box.label(text="请选择一个相机对象", icon='INFO')
            return

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator(OBJECT_OT_quick_settings_camera.bl_idname, text="打开快捷弹窗", icon='WINDOW')

        draw_camera_ui(layout, context, obj, show_view_controls=True)


# =========================
# 弹窗 Operator（无标题、无确定/取消按钮）
# =========================

class OBJECT_OT_quick_settings_camera(bpy.types.Operator):
    bl_idname = "object.quick_settings_camera"
    bl_label = "快速设置相机"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}   # INTERNAL 隐藏底部 UI 和部分窗口元素

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'CAMERA'

    def invoke(self, context, event):
        prefs = get_addon_prefs()
        width = prefs.popup_width if prefs else 240
        # invoke_popup 代替默认以去掉底部确认取消
        return context.window_manager.invoke_popup(self, width=width)

    def draw(self, context):
        draw_camera_ui(self.layout, context, context.active_object)

    def execute(self, context):
        return {'FINISHED'}


class CAMERA_OT_align_to_view(bpy.types.Operator):
    bl_idname = "camera.align_to_view"
    bl_label = "相机对齐视图"
    bl_description = "将活动相机对齐到当前 3D 视图"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        try:
            bpy.ops.view3d.camera_to_view()
        except Exception as e:
            self.report({'ERROR'}, f"无法对齐视图：{e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class CAMERA_OT_view_from_camera(bpy.types.Operator):
    bl_idname = "camera.view_from_camera"
    bl_label = "进入相机视图"
    bl_description = "将当前 3D 视图切换为活动相机视角"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        try:
            bpy.ops.view3d.view_camera()
        except Exception as e:
            self.report({'ERROR'}, f"无法进入相机视图：{e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class CAMERA_OT_focus_selected(bpy.types.Operator):
    bl_idname = "camera.focus_selected"
    bl_label = "聚焦选中物体"
    bl_description = "将景深焦点设为同时选中的目标物体并开启景深（需相机与一个目标物体同时选中）"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'CAMERA'

    def execute(self, context):
        cam = context.active_object
        targets = [o for o in context.selected_objects if o != cam and o.type != 'CAMERA']
        if len(targets) != 1:
            self.report({'WARNING'}, "请同时选中相机和一个目标物体")
            return {'CANCELLED'}
        cam.data.dof.focus_object = targets[0]
        cam.data.dof.use_dof = True
        self.report({'INFO'}, f"景深焦点已设为 {targets[0].name}")
        return {'FINISHED'}


# =========================
# 注册
# =========================

classes = (
    QUICKCAM_AddonPreferences,
    QUICKCAM_ModuleVisibility,
    CAMERA_OT_set_focal_length,
    CAMERA_OT_set_fstop,
    CAMERA_OT_enable_passepartout,
    CAMERA_OT_align_to_view,
    CAMERA_OT_view_from_camera,
    CAMERA_OT_focus_selected,
    OBJECT_OT_quick_settings_camera,
    VIEW3D_PT_quick_settings_camera,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.quickcam_module_visibility = bpy.props.PointerProperty(type=QUICKCAM_ModuleVisibility)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(OBJECT_OT_quick_settings_camera.bl_idname, 'D', 'PRESS')
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()

    if hasattr(bpy.types.Scene, "quickcam_module_visibility"):
        del bpy.types.Scene.quickcam_module_visibility

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
