"""Tool Bar for Annotation Tools"""

from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel, QComboBox, QSpinBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QAction, QActionGroup


class ToolBar(QToolBar):
    """标注工具栏"""

    tool_changed = pyqtSignal(str)  # Tool name
    class_changed = pyqtSignal(str, str)  # Class name, color

    def __init__(self, parent=None):
        super().__init__("工具栏", parent)
        self.setMovable(False)

        self.current_tool = "point"
        self.current_class = "object"
        self.classes = [
            {"name": "object", "color": "#00ff00"},
            {"name": "person", "color": "#ff0000"},
            {"name": "car", "color": "#0000ff"},
        ]

        # 设置工具栏样式，突出显示选中的工具
        self.setStyleSheet("""
            QToolBar {
                background-color: #2a2a2a;
                border: 1px solid #5a5a5a;
                padding: 5px;
            }
            QToolBar QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QToolBar QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 5px;
            }
            QToolBar::separator {
                background-color: #5a5a5a;
                width: 1px;
                margin: 5px;
            }
            QToolButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid transparent;
                border-radius: 4px;
                padding: 8px 12px;
                margin: 2px;
                font-weight: normal;
            }
            QToolButton:hover {
                background-color: #4a4a4a;
                border-color: #6a6a6a;
            }
            QToolButton:checked {
                background-color: #336699;
                border-color: #4477aa;
                font-weight: bold;
            }
            QToolButton:checked:hover {
                background-color: #4477aa;
            }
        """)

        self.init_tools()
        self.init_class_selector()

    def init_tools(self):
        """初始化工具按钮"""
        # Create action group for exclusive selection
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        # Point tool
        point_action = QAction("点点击", self)
        point_action.setCheckable(True)
        point_action.setChecked(True)
        point_action.setToolTip("使用SAM2进行点点击分割")
        point_action.setShortcut(QKeySequence("1"))
        point_action.triggered.connect(lambda: self.set_tool("point"))
        tool_group.addAction(point_action)
        self.addAction(point_action)

        # Box tool
        box_action = QAction("边界框", self)
        box_action.setCheckable(True)
        box_action.setToolTip("使用SAM2进行边界框分割")
        box_action.setShortcut(QKeySequence("2"))
        box_action.triggered.connect(lambda: self.set_tool("box"))
        tool_group.addAction(box_action)
        self.addAction(box_action)

        # Polygon tool
        polygon_action = QAction("多边形", self)
        polygon_action.setCheckable(True)
        polygon_action.setToolTip("手动绘制多边形")
        polygon_action.setShortcut(QKeySequence("3"))
        polygon_action.triggered.connect(lambda: self.set_tool("polygon"))
        tool_group.addAction(polygon_action)
        self.addAction(polygon_action)

        # Edit tool
        edit_action = QAction("编辑", self)
        edit_action.setCheckable(True)
        edit_action.setToolTip("选择和编辑标注")
        edit_action.setShortcut(QKeySequence("4"))
        edit_action.triggered.connect(lambda: self.set_tool("edit"))
        tool_group.addAction(edit_action)
        self.addAction(edit_action)

        self.addSeparator()

    def init_class_selector(self):
        """初始化类别选择器"""
        # Class label
        class_label = QLabel("类别:")
        self.addWidget(class_label)

        # Class combo box
        self.class_combo = QComboBox()
        for cls in self.classes:
            self.class_combo.addItem(cls["name"])
        self.class_combo.currentTextChanged.connect(self.on_class_changed)
        self.addWidget(self.class_combo)

        self.addSeparator()

        # View toggles
        self.show_masks_action = QAction("显示掩码", self)
        self.show_masks_action.setCheckable(True)
        self.show_masks_action.setChecked(True)
        self.addAction(self.show_masks_action)

        self.show_polygons_action = QAction("显示多边形", self)
        self.show_polygons_action.setCheckable(True)
        self.show_polygons_action.setChecked(True)
        self.addAction(self.show_polygons_action)

        self.show_bbox_action = QAction("显示边界框", self)
        self.show_bbox_action.setCheckable(True)
        self.show_bbox_action.setChecked(True)
        self.addAction(self.show_bbox_action)

    def set_tool(self, tool: str):
        """设置当前工具"""
        self.current_tool = tool
        self.tool_changed.emit(tool)

    def on_class_changed(self, class_name: str):
        """类别更改"""
        for cls in self.classes:
            if cls["name"] == class_name:
                self.current_class = class_name
                self.class_changed.emit(class_name, cls["color"])
                return

    def set_classes(self, classes: list):
        """设置类别列表"""
        self.classes = classes
        self.class_combo.clear()
        for cls in classes:
            self.class_combo.addItem(cls["name"])

    def get_current_class(self) -> tuple:
        """获取当前类别"""
        return (self.current_class, self.classes[self.class_combo.currentIndex()]["color"])