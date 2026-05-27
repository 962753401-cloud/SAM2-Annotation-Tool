"""Layer List for Annotations - 右侧标注操作面板"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QHBoxLayout, QPushButton, QLabel, QComboBox, QMenu,
    QLineEdit, QTextEdit, QGroupBox, QSplitter, QMessageBox,
    QFileDialog, QDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QBrush, QPen, QFont
from typing import List, Optional
import json
import os
import uuid
from ..core.annotation_data import Annotation


class LayerList(QWidget):
    """标注列表控件 - 模型识别+人工录入信息标注操作栏目"""

    annotation_clicked = pyqtSignal(int)
    annotation_deleted = pyqtSignal(int)
    annotation_confirmed = pyqtSignal(int)  # 确认标注信号
    annotation_adjusted = pyqtSignal(int)   # 微调标注信号
    annotation_added = pyqtSignal(object)   # 新增：标注添加信号，传递Annotation对象
    annotations_changed = pyqtSignal(list)  # 新增：标注列表变更信号
    annotations_loaded = pyqtSignal(list)   # 新增：从文件加载标注信号
    canvas_update_requested = pyqtSignal()  # 新增：请求更新canvas信号
    class_changed = pyqtSignal(int, str)
    visibility_changed = pyqtSignal(int, bool)
    label_changed = pyqtSignal(int, str)
    save_annotations = pyqtSignal()  # 保存所有标注信号
    save_coco_requested = pyqtSignal()  # 保存COCO格式
    save_voc_requested = pyqtSignal()  # 保存VOC格式

    def __init__(self, parent=None):
        super().__init__(parent)

        self.annotations: List[Annotation] = []
        self.selected_id: Optional[int] = None
        self.annotation_file_path: str = ""  # 当前标注文件路径

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # === 模型识别结果列表 ===
        result_group = QGroupBox("模型识别结果")
        result_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #5a5a5a; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        result_layout = QVBoxLayout(result_group)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("QListWidget { background-color: #2a2a2a; } QListWidget::item { padding: 5px; } QListWidget::item:selected { background-color: #5a5a5a; }")
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        result_layout.addWidget(self.list_widget)

        # List buttons
        list_btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #aa3333; color: #ffffff; padding: 5px; }")
        self.delete_btn.clicked.connect(self.delete_selected)
        list_btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("清除全部")
        self.clear_btn.setStyleSheet("QPushButton { background-color: #666666; color: #ffffff; padding: 5px; }")
        self.clear_btn.clicked.connect(self.clear_all)
        list_btn_layout.addWidget(self.clear_btn)
        result_layout.addLayout(list_btn_layout)

        layout.addWidget(result_group)

        # === 人工录入信息标注操作 ===
        self.input_group = QGroupBox("人工录入信息标注")
        self.input_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #5a5a5a; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        input_layout = QVBoxLayout(self.input_group)

        # Current selection info
        self.selection_info = QLabel("未选中标注")
        self.selection_info.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        input_layout.addWidget(self.selection_info)

        # Class selector
        class_layout = QHBoxLayout()
        class_label = QLabel("类别:")
        class_label.setStyleSheet("color: #ffffff;")
        class_layout.addWidget(class_label)

        self.class_combo = QComboBox()
        self.class_combo.addItems(["object", "person", "car", "animal", "vehicle", "building", "tree", "other"])
        self.class_combo.setStyleSheet("QComboBox { background-color: #3a3a3a; color: #ffffff; padding: 5px; } QComboBox::drop-down { border: 1px solid #5a5a5a; }")
        self.class_combo.currentTextChanged.connect(self.on_class_combo_changed)
        class_layout.addWidget(self.class_combo)
        input_layout.addLayout(class_layout)

        # Label text input
        label_layout = QVBoxLayout()
        label_header = QLabel("文本标注内容:")
        label_header.setStyleSheet("color: #ffffff;")
        label_layout.addWidget(label_header)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("输入物品名称、描述等信息...")
        self.label_edit.setStyleSheet("QLineEdit { background-color: #3a3a3a; color: #ffffff; padding: 8px; border: 1px solid #5a5a5a; }")
        # 使用 editingFinished 信号，只在用户完成编辑时触发（按回车或失去焦点）
        # 不会在 setText() 时触发，避免递归崩溃
        self.label_edit.editingFinished.connect(self.on_label_editing_finished)
        label_layout.addWidget(self.label_edit)
        input_layout.addLayout(label_layout)

        # Adjust boundary button
        adjust_layout = QHBoxLayout()
        self.adjust_btn = QPushButton("微调边界")
        self.adjust_btn.setStyleSheet("QPushButton { background-color: #336699; color: #ffffff; padding: 8px; } QPushButton:hover { background-color: #4477aa; }")
        self.adjust_btn.clicked.connect(self.adjust_selected)
        self.adjust_btn.setToolTip("选中后可在画布上拖拽顶点微调边界")
        adjust_layout.addWidget(self.adjust_btn)

        self.confirm_btn = QPushButton("确认此标注")
        self.confirm_btn.setStyleSheet("QPushButton { background-color: #33aa33; color: #ffffff; padding: 8px; } QPushButton:hover { background-color: #44bb44; }")
        self.confirm_btn.clicked.connect(self.confirm_selected)
        self.confirm_btn.setToolTip("确认当前标注为有效标注")
        adjust_layout.addWidget(self.confirm_btn)
        input_layout.addLayout(adjust_layout)

        layout.addWidget(self.input_group)

        # === 保存完整标注数据 ===
        save_group = QGroupBox("保存标注数据")
        save_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #5a5a5a; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        save_layout = QVBoxLayout(save_group)

        # Statistics
        self.stats_label = QLabel("标注统计: 0 个对象")
        self.stats_label.setStyleSheet("color: #aaaaaa;")
        save_layout.addWidget(self.stats_label)

        # Save buttons
        save_btn_layout = QHBoxLayout()

        self.save_coco_btn = QPushButton("保存COCO格式")
        self.save_coco_btn.setStyleSheet("QPushButton { background-color: #555599; color: #ffffff; padding: 10px; } QPushButton:hover { background-color: #6666aa; }")
        self.save_coco_btn.clicked.connect(self.save_coco_requested.emit)
        save_btn_layout.addWidget(self.save_coco_btn)

        self.save_voc_btn = QPushButton("保存VOC格式")
        self.save_voc_btn.setStyleSheet("QPushButton { background-color: #995555; color: #ffffff; padding: 10px; } QPushButton:hover { background-color: #aa6666; }")
        self.save_voc_btn.clicked.connect(self.save_voc_requested.emit)
        save_btn_layout.addWidget(self.save_voc_btn)

        save_layout.addLayout(save_btn_layout)

        # Export all button
        self.export_all_btn = QPushButton("导出全部标注数据")
        self.export_all_btn.setStyleSheet("QPushButton { background-color: #339933; color: #ffffff; padding: 10px; font-weight: bold; } QPushButton:hover { background-color: #44aa44; }")
        self.export_all_btn.clicked.connect(lambda: self.save_annotations.emit())
        save_layout.addWidget(self.export_all_btn)

        layout.addWidget(save_group)

        # === 查看标注数据文件 ===
        view_group = QGroupBox("查看标注数据文件")
        view_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #5a5a5a; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        view_layout = QVBoxLayout(view_group)

        # File path display
        self.file_path_label = QLabel("未加载标注文件")
        self.file_path_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.file_path_label.setWordWrap(True)
        view_layout.addWidget(self.file_path_label)

        # View buttons
        view_btn_layout = QHBoxLayout()

        self.load_btn = QPushButton("加载标注文件")
        self.load_btn.setStyleSheet("QPushButton { background-color: #555555; color: #ffffff; padding: 8px; } QPushButton:hover { background-color: #666666; }")
        self.load_btn.clicked.connect(self.load_annotation_file)
        view_btn_layout.addWidget(self.load_btn)

        self.view_btn = QPushButton("查看数据内容")
        self.view_btn.setStyleSheet("QPushButton { background-color: #555555; color: #ffffff; padding: 8px; } QPushButton:hover { background-color: #666666; }")
        self.view_btn.clicked.connect(self.view_annotation_data)
        view_btn_layout.addWidget(self.view_btn)

        view_layout.addLayout(view_btn_layout)

        layout.addWidget(view_group)

        # Initially hide input group
        self.input_group.setVisible(False)

    def set_annotations(self, annotations: List[Annotation]):
        """设置标注列表"""
        self.annotations = annotations.copy()
        self.update_list()
        self.update_stats()

    def add_annotation(self, annotation: Annotation):
        """添加标注"""
        self.annotations.append(annotation)
        self.add_list_item(annotation)
        self.update_stats()

    def remove_annotation(self, annotation_id: int):
        """从列表中移除标注"""
        # Remove from annotations list
        self.annotations = [a for a in self.annotations if a.id != annotation_id]

        # Remove from list widget
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == annotation_id:
                self.list_widget.takeItem(i)
                break

        # Clear selection if this was selected
        if self.selected_id == annotation_id:
            self.selected_id = None
            self.selection_info.setText("未选中标注")
            self.input_group.setVisible(False)

        self.update_stats()

    def clear_annotations(self):
        """清除所有标注"""
        self.annotations.clear()
        self.list_widget.clear()
        self.selected_id = None
        self.selection_info.setText("未选中标注")
        self.input_group.setVisible(False)
        self.update_stats()

    def update_list(self):
        """更新列表"""
        self.list_widget.clear()
        for ann in self.annotations:
            self.add_list_item(ann)

    def update_stats(self):
        """更新统计信息"""
        confirmed_count = sum(1 for a in self.annotations if a.label)
        total_count = len(self.annotations)
        self.stats_label.setText(f"标注统计: {total_count} 个对象 (已标注: {confirmed_count})")

    def add_list_item(self, annotation: Annotation):
        """添加列表项"""
        item = QListWidgetItem()

        # Format text with label
        text = f"[{annotation.class_name}] ID:{annotation.id}"

        if annotation.label:
            text += f"\n标注: {annotation.label}"

        area = annotation.get_area()
        text += f"\n面积: {area}px"

        if annotation.confidence > 0:
            text += f"\n置信度: {annotation.confidence:.2f}"

        item.setText(text)
        item.setData(Qt.ItemDataRole.UserRole, annotation.id)

        # Red color for unconfirmed, green for confirmed
        if annotation.label:
            item.setForeground(QBrush(QColor(0, 255, 0)))  # Green for confirmed
        else:
            item.setForeground(QBrush(QColor(255, 0, 0)))  # Red for unconfirmed

        # Show visibility indicator
        if not annotation.visible:
            item.setForeground(QBrush(QColor(100, 100, 100)))

        self.list_widget.addItem(item)

    def on_item_clicked(self, item: QListWidgetItem):
        """项点击"""
        annotation_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_id = annotation_id
        self.annotation_clicked.emit(annotation_id)
        self.update_info_panel(annotation_id)

    def update_info_panel(self, annotation_id: int):
        """更新信息面板"""
        ann = self.get_annotation(annotation_id)

        if ann:
            self.input_group.setVisible(True)
            self.class_combo.setCurrentText(ann.class_name)
            self.label_edit.setText(ann.label)  # 安全：editingFinished 不会在 setText 时触发
            self.selection_info.setText(f"选中: {ann.class_name} (ID:{ann.id}) | 面积: {ann.get_area()}px")
        else:
            self.input_group.setVisible(False)
            self.selection_info.setText("未选中标注")

    def on_item_double_clicked(self, item: QListWidgetItem):
        """项双击 - 编辑标注"""
        annotation_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_id = annotation_id
        self.annotation_clicked.emit(annotation_id)
        self.update_info_panel(annotation_id)
        self.label_edit.setFocus()

    def on_class_combo_changed(self, class_name: str):
        """类别下拉框变更"""
        if self.selected_id:
            self.class_changed.emit(self.selected_id, class_name)
            ann = self.get_annotation(self.selected_id)
            if ann:
                ann.class_name = class_name
                self.update_list_item(self.selected_id)

    def on_label_editing_finished(self):
        """文本标注编辑完成 - 用户按回车或失去焦点时触发"""
        if not self.selected_id:
            return

        text = self.label_edit.text()
        ann = self.get_annotation(self.selected_id)

        if ann:
            ann.label = text
            self.label_changed.emit(self.selected_id, text)
            self.update_list_item(self.selected_id)
            self.update_stats()
            # 更新canvas显示
            self.canvas_update_requested.emit()

    def update_list_item(self, annotation_id: int):
        """更新单个列表项显示"""
        ann = self.get_annotation(annotation_id)
        if not ann:
            return

        try:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == annotation_id:
                    # Update text
                    text = f"[{ann.class_name}] ID:{ann.id}"

                    if ann.label:
                        text += f"\n标注: {ann.label}"

                    area = ann.get_area()
                    text += f"\n面积: {area}px"

                    if ann.confidence > 0:
                        text += f"\n置信度: {ann.confidence:.2f}"

                    item.setText(text)

                    # Update color
                    if ann.label:
                        item.setForeground(QBrush(QColor(0, 255, 0)))
                    else:
                        item.setForeground(QBrush(QColor(255, 0, 0)))
                    break
        except Exception as e:
            print(f"Error updating list item: {e}")

    def show_context_menu(self, pos: QPoint):
        """显示右键菜单"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        annotation_id = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #3a3a3a; color: #ffffff; }")

        # Edit actions
        edit_label_action = menu.addAction("编辑标注文本")
        adjust_action = menu.addAction("微调边界")
        confirm_action = menu.addAction("确认标注")

        menu.addSeparator()

        # Class change
        change_class_menu = menu.addMenu("更改类别")
        for cls in ["object", "person", "car", "animal", "vehicle", "building", "tree", "other"]:
            change_class_menu.addAction(cls)

        # Visibility action
        ann = self.get_annotation(annotation_id)
        visibility_action = None
        if ann:
            visibility_action = menu.addAction(
                "显示" if not ann.visible else "隐藏"
            )

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("删除")

        action = menu.exec(self.list_widget.mapToGlobal(pos))

        if action == delete_action:
            self.do_delete(annotation_id)

        elif action == visibility_action and ann:
            self.visibility_changed.emit(annotation_id, not ann.visible)

        elif action == edit_label_action:
            self.selected_id = annotation_id
            self.annotation_clicked.emit(annotation_id)
            self.update_info_panel(annotation_id)
            self.label_edit.setFocus()

        elif action == adjust_action:
            self.annotation_adjusted.emit(annotation_id)

        elif action == confirm_action:
            self.annotation_confirmed.emit(annotation_id)

        # Handle class change
        if action and action.text() in ["object", "person", "car", "animal", "vehicle", "building", "tree", "other"]:
            self.class_changed.emit(annotation_id, action.text())
            ann = self.get_annotation(annotation_id)
            if ann:
                ann.class_name = action.text()
                self.update_list_item(annotation_id)

    def do_delete(self, annotation_id: int):
        """执行删除操作"""
        # Remove from annotations list first
        self.annotations = [a for a in self.annotations if a.id != annotation_id]

        # Remove from list widget
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == annotation_id:
                self.list_widget.takeItem(i)
                break

        # Emit signal to update canvas and project
        self.annotation_deleted.emit(annotation_id)

        # Clear selection
        if self.selected_id == annotation_id:
            self.selected_id = None
            self.selection_info.setText("未选中标注")
            self.input_group.setVisible(False)

        self.update_stats()

    def delete_selected(self):
        """删除选中项"""
        if self.selected_id:
            self.do_delete(self.selected_id)

    def clear_all(self):
        """清除所有"""
        if not self.annotations:
            return

        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除所有标注吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete each annotation
            for ann in self.annotations:
                self.annotation_deleted.emit(ann.id)
            self.clear_annotations()

    def adjust_selected(self):
        """微调选中标注的边界"""
        if self.selected_id:
            self.annotation_adjusted.emit(self.selected_id)

    def confirm_selected(self):
        """确认选中标注 - 完整异常保护"""
        if not self.selected_id:
            return

        try:
            ann = self.get_annotation(self.selected_id)
            if not ann:
                return

            # 保存当前选中ID，用于后续操作
            current_id = self.selected_id
            class_name = ann.class_name
            label_text = ann.label or "已确认"

            # 先更新数据
            ann.label = label_text

            # 发射信号通知其他组件
            self.annotation_confirmed.emit(current_id)

            # 更新列表显示（在QMessageBox之前）
            self.update_list_item(current_id)
            self.update_stats()

            # 先隐藏面板和清除选中状态（在QMessageBox之前）
            self.input_group.setVisible(False)
            self.selected_id = None
            self.selection_info.setText("未选中标注")

            # 最后显示成功提示（使用非阻塞方式）
            QMessageBox.information(
                self,
                "确认成功",
                f"标注 ID:{current_id} 已确认成功！\n类别: {class_name}\n标注: {label_text}"
            )

        except Exception as e:
            print(f"Error in confirm_selected: {e}")
            # 发生异常时也要清除状态
            self.selected_id = None
            self.selection_info.setText("未选中标注")

    def get_selected_annotation(self) -> Optional[int]:
        """获取选中的标注ID"""
        return self.selected_id

    def select_annotation(self, annotation_id: int):
        """选择标注"""
        self.selected_id = annotation_id
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == annotation_id:
                self.list_widget.setCurrentItem(item)
                break
        self.update_info_panel(annotation_id)

    def get_annotation(self, annotation_id: int) -> Optional[Annotation]:
        """获取标注对象"""
        for ann in self.annotations:
            if ann.id == annotation_id:
                return ann
        return None

    def get_all_annotations(self) -> List[Annotation]:
        """获取所有标注"""
        return self.annotations.copy()

    def load_annotation_file(self):
        """加载标注文件并解析数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "加载标注文件",
            "",
            "Annotation Files (*.json *.xml);;JSON Files (*.json);;XML Files (*.xml);;All Files (*)"
        )

        if not file_path:
            return

        self.annotation_file_path = file_path
        self.file_path_label.setText(f"已加载: {os.path.basename(file_path)}")
        self.file_path_label.setStyleSheet("color: #33aa33; font-size: 11px;")

        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.parse_coco_data(data)
            else:
                QMessageBox.warning(self, "提示", "暂不支持该格式")
                return

            QMessageBox.information(self, "成功", f"已加载 {len(self.annotations)} 个标注")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件: {e}")

    def parse_coco_data(self, data):
        """解析COCO格式数据并加载到标注列表"""
        # 清空现有标注
        self.annotations.clear()
        self.list_widget.clear()

        # 解析标注数据
        annotations_data = data.get("annotations", [])

        for ann_data in annotations_data:
            # 创建标注对象
            ann = Annotation()
            ann.id = ann_data.get("id", int(uuid.uuid4().int % 1000000))

            # 获取类别名称
            category_id = ann_data.get("category_id", 0)
            categories = data.get("categories", [])
            for cat in categories:
                if cat.get("id") == category_id:
                    ann.class_name = cat.get("name", "object")
                    break
            ann.class_id = category_id

            # 解析polygon (segmentation)
            segmentation = ann_data.get("segmentation", [])
            if segmentation and len(segmentation) > 0:
                # COCO格式: [[x1,y1,x2,y2,...]]
                poly_flat = segmentation[0]
                polygon = []
                for i in range(0, len(poly_flat), 2):
                    if i + 1 < len(poly_flat):
                        polygon.append([int(poly_flat[i]), int(poly_flat[i+1])])
                ann.polygon = polygon

            # 解析bbox
            bbox = ann_data.get("bbox", [0, 0, 0, 0])
            ann.bbox = bbox

            # 计算面积
            ann.confidence = ann_data.get("attributes", {}).get("confidence", 0.0)
            ann.label = ann_data.get("attributes", {}).get("label", "")
            ann.is_manual = ann_data.get("attributes", {}).get("is_manual", False)

            # 添加到列表
            self.annotations.append(ann)
            self.add_list_item(ann)

        self.update_stats()

        # 发射信号通知canvas更新
        self.annotations_loaded.emit(self.annotations)

    def view_annotation_data(self):
        """查看标注数据内容"""
        if not self.annotation_file_path:
            # Show current annotations if no file loaded
            if self.annotations:
                self.show_current_annotations()
            else:
                QMessageBox.information(self, "提示", "没有可查看的标注数据")
            return

        # Read and display file content
        try:
            if self.annotation_file_path.endswith('.json'):
                with open(self.annotation_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.show_json_data(data)
            else:
                with open(self.annotation_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.show_text_data(content)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件: {e}")

    def show_current_annotations(self):
        """显示当前标注数据"""
        # Create summary
        summary = f"当前标注数据汇总:\n\n"
        summary += f"总标注数量: {len(self.annotations)}\n"

        confirmed = sum(1 for a in self.annotations if a.label)
        summary += f"已标注数量: {confirmed}\n"
        summary += f"未标注数量: {len(self.annotations) - confirmed}\n\n"

        summary += "详细列表:\n"
        for ann in self.annotations:
            summary += f"\n[ID:{ann.id}] {ann.class_name}"
            if ann.label:
                summary += f" - 标注: {ann.label}"
            summary += f" - 面积: {ann.get_area()}px"

        self.show_text_data(summary)

    def show_json_data(self, data):
        """显示JSON数据"""
        # Format JSON nicely
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.show_text_data(formatted)

    def show_text_data(self, text):
        """显示文本数据对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("标注数据内容")
        dialog.setMinimumSize(600, 400)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Create text display
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setStyleSheet("QTextEdit { background-color: #1a1a1a; color: #ffffff; }")
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        # Close button
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def set_file_path(self, path: str):
        """设置标注文件路径"""
        self.annotation_file_path = path
        if path:
            self.file_path_label.setText(f"已加载: {os.path.basename(path)}")
            self.file_path_label.setStyleSheet("color: #33aa33; font-size: 11px;")
        else:
            self.file_path_label.setText("未加载标注文件")
            self.file_path_label.setStyleSheet("color: #888888; font-size: 11px;")