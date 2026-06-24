"""Main Window for SAM2 Annotation Tool"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QLabel,
    QStatusBar, QApplication, QDockWidget, QMenu, QMenuBar, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon, QKeySequence, QAction

from .canvas_widget import CanvasWidget
from .image_list import ImageList
from .layer_list import LayerList
from .tool_bar import ToolBar
from ..core.sam2_engine import SAM2Engine
from ..core.image_manager import ImageManager
from ..core.project_manager import ProjectManager
from ..core.annotation_data import Annotation, ImageAnnotation
from ..utils.config_loader import ConfigLoader


class MainWindow(QMainWindow):
    """SAM2标注工具主窗口"""

    def __init__(self, config_path: str = None):
        super().__init__()

        # Load configuration
        self.config = ConfigLoader(config_path)

        # Initialize components
        self.sam2_engine = None
        self.image_manager = ImageManager()
        self.project_manager = ProjectManager()

        # Current state
        self.current_tool = "point"  # point, box, polygon, edit
        self.current_class = "object"
        self.current_color = "#ff0000"  # 默认红色描边

        # Setup UI
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.init_connections()

        # Apply theme
        self.apply_theme()

        # Window settings
        self.setWindowTitle("SAM2 Annotation Tool")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Load SAM2 model after UI is ready
        QTimer.singleShot(100, self.load_model)

    def init_ui(self):
        """初始化UI布局"""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Image list
        self.image_list = ImageList()
        self.image_list.setMinimumWidth(200)
        self.image_list.setMaximumWidth(400)
        splitter.addWidget(self.image_list)

        # Center panel: Canvas
        self.canvas = CanvasWidget()
        splitter.addWidget(self.canvas)

        # Right panel: Annotation list
        self.layer_list = LayerList()
        self.layer_list.setMinimumWidth(200)
        self.layer_list.setMaximumWidth(400)
        splitter.addWidget(self.layer_list)

        # Set splitter proportions
        splitter.setSizes([250, 800, 250])

        main_layout.addWidget(splitter)

    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("文件")

        open_folder_action = QAction("打开文件夹", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+O"))
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        open_image_action = QAction("打开图片", self)
        open_image_action.triggered.connect(self.open_image)
        file_menu.addAction(open_image_action)

        file_menu.addSeparator()

        new_project_action = QAction("新建项目", self)
        new_project_action.setShortcut(QKeySequence("Ctrl+N"))
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("打开项目", self)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        save_project_action = QAction("保存项目", self)
        save_project_action.setShortcut(QKeySequence("Ctrl+S"))
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)

        file_menu.addSeparator()

        export_action = QAction("导出标注", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_annotations)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("编辑")

        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("删除标注", self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self.delete_selected_annotation)
        edit_menu.addAction(delete_action)

        clear_action = QAction("清除所有标注", self)
        clear_action.triggered.connect(self.clear_all_annotations)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("视图")

        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("适应窗口", self)
        fit_action.setShortcut(QKeySequence("Ctrl+0"))
        fit_action.triggered.connect(self.canvas.fit_to_window)
        view_menu.addAction(fit_action)

        # Help menu
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_toolbar(self):
        """初始化工具栏"""
        self.tool_bar = ToolBar(self)
        self.addToolBar(self.tool_bar)

    def init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label, 1)

        self.image_info_label = QLabel("")
        self.statusbar.addPermanentWidget(self.image_info_label)

        self.model_status_label = QLabel("模型未加载")
        self.statusbar.addPermanentWidget(self.model_status_label)

    def init_connections(self):
        """初始化信号连接"""
        # Image list signals
        self.image_list.image_selected.connect(self.on_image_selected)

        # Canvas signals
        self.canvas.point_clicked.connect(self.on_point_clicked)
        self.canvas.box_drawn.connect(self.on_box_drawn)
        self.canvas.polygon_drawn.connect(self.on_polygon_drawn)
        self.canvas.annotation_selected.connect(self.on_annotation_selected)

        # Layer list signals
        self.layer_list.annotation_clicked.connect(self.on_annotation_clicked)
        self.layer_list.annotation_deleted.connect(self.on_annotation_deleted)
        self.layer_list.annotation_confirmed.connect(self.on_annotation_confirmed)
        self.layer_list.annotation_adjusted.connect(self.on_annotation_adjusted)
        self.layer_list.annotations_loaded.connect(self.on_annotations_loaded)
        self.layer_list.canvas_update_requested.connect(self.on_canvas_update_requested)
        self.layer_list.save_annotations.connect(self.export_annotations)
        self.layer_list.save_coco_requested.connect(self.save_coco_format)
        self.layer_list.save_voc_requested.connect(self.save_voc_format)
        self.layer_list.class_changed.connect(self.on_class_changed)
        self.layer_list.visibility_changed.connect(self.on_visibility_changed)
        self.layer_list.label_changed.connect(self.on_label_changed)

        # Tool bar signals
        self.tool_bar.tool_changed.connect(self.on_tool_changed)
        self.tool_bar.class_changed.connect(self.on_class_changed_tool)

    def apply_theme(self):
        """应用主题"""
        theme = self.config.get("ui.theme", "dark")

        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2a2a2a;
                }
                QWidget {
                    background-color: #2a2a2a;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #3a3a3a;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #5a5a5a;
                }
                QMenu {
                    background-color: #3a3a3a;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #5a5a5a;
                }
                QStatusBar {
                    background-color: #3a3a3a;
                    color: #ffffff;
                }
                QToolBar {
                    background-color: #3a3a3a;
                    border: none;
                }
                QSplitter::handle {
                    background-color: #5a5a5a;
                }
            """)

    def load_model(self):
        """加载SAM2模型"""
        self.status_label.setText("正在加载SAM2模型...")
        self.model_status_label.setText("加载中...")

        model_path = self.config.get("model.path", "")
        config_path = self.config.get("model.config_path", "")
        device = self.config.get("model.device", "cuda")

        self.sam2_engine = SAM2Engine(model_path, config_path, device)

        if self.sam2_engine.load_model():
            self.status_label.setText("模型加载成功")
            self.model_status_label.setText("SAM2就绪")
        else:
            self.status_label.setText("模型加载失败")
            self.model_status_label.setText("错误")
            QMessageBox.warning(
                self,
                "警告",
                "SAM2模型加载失败，请检查模型路径和依赖安装。\n"
                "标注功能可能受限。"
            )

    def open_folder(self):
        """打开图片文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择图片文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            # Clear existing images first
            self.image_manager.clear()
            images = self.image_manager.load_images_from_dir(folder)
            self.image_list.set_images(images)
            self.status_label.setText(f"已加载 {len(images)} 张图片")

            if images:
                self.load_current_image()

    def open_image(self):
        """打开图片（支持多选）"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片（可多选）",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;All Files (*)"
        )

        if file_paths:
            # Add to existing images
            for file_path in file_paths:
                if file_path not in self.image_manager.images:
                    self.image_manager.images.append(file_path)

            # Sort images
            self.image_manager.images.sort()

            # Set current index to first new image
            if self.image_manager.current_index < 0:
                self.image_manager.current_index = 0

            # Update image list display
            self.image_list.set_images(self.image_manager.images)
            self.status_label.setText(f"已加载 {len(self.image_manager.images)} 张图片")

            # Load current image
            self.image_manager.load_current_image()
            self.load_current_image()

    def open_multiple_images(self):
        """打开多张图片"""
        self.open_image()

    def load_current_image(self):
        """加载当前图像到画布"""
        image = self.image_manager.current_image
        if image is None:
            print("Warning: No current image loaded")
            self.status_label.setText("图片加载失败")
            return

        image_path = self.image_manager.get_current_image_path()
        if image_path is None:
            print("Warning: No current image path")
            return

        image_size = self.image_manager.get_current_image_size()
        print(f"Loading image: {image_path}, size: {image_size}")

        # Ensure project exists
        if self.project_manager.project is None:
            self.project_manager.create_project("默认项目", "")

        # Set image to canvas
        self.canvas.set_image(image)

        # Set image to SAM2
        if self.sam2_engine and self.sam2_engine.is_loaded:
            self.sam2_engine.set_image(image)

        # Update image info
        self.image_info_label.setText(
            f"{os.path.basename(image_path)} | {image_size[0]}x{image_size[1]}"
        )

        # Load existing annotations
        if self.project_manager.project:
            img_ann = self.project_manager.get_image_annotation(image_path)
            if img_ann:
                self.layer_list.set_annotations(img_ann.annotations)
                self.canvas.set_annotations(img_ann.annotations)
            else:
                # Create new image annotation
                self.project_manager.add_image_to_project(image_path, image_size)
                self.layer_list.clear_annotations()
                self.canvas.clear_annotations()

        self.status_label.setText("图片已加载，可以开始标注")

    def on_image_selected(self, image_path: str):
        """图片选择回调"""
        index = self.image_manager.get_index_by_path(image_path)
        if index >= 0:
            self.image_manager.load_image(index)
            self.load_current_image()

    def on_point_clicked(self, point: tuple):
        """点点击回调 - SAM2分割"""
        if not self.sam2_engine or not self.sam2_engine.is_loaded:
            self.status_label.setText("SAM2模型未加载，无法进行分割")
            return

        self.status_label.setText("正在进行分割...")

        # Run SAM2 prediction
        masks, scores, _ = self.sam2_engine.predict_from_points([list(point)])

        if masks is not None:
            # Get best mask
            best_mask = self.sam2_engine.get_best_mask(masks, scores)
            best_score = float(scores.max()) if scores is not None else 0.0

            # Convert to polygon and bbox
            polygon = self.sam2_engine.mask_to_polygon(best_mask)
            bbox = self.sam2_engine.mask_to_bbox(best_mask)

            # Debug: 检查 polygon 数据
            print(f"[DEBUG] mask_to_polygon result: {len(polygon) if polygon else 0} points")
            print(f"[DEBUG] mask_to_bbox result: {bbox}")
            if polygon:
                print(f"[DEBUG] First 3 polygon points: {polygon[:3]}")

            # Create annotation
            annotation = Annotation(
                class_name=self.current_class,
                mask=best_mask,
                polygon=polygon,
                bbox=bbox,
                confidence=best_score,
                color=self.current_color
            )

            # 计算质量指标
            annotation.calculate_quality_metrics(self.config.get_quality_config())

            # Debug: 检查 annotation 创建后的数据
            print(f"[DEBUG] Annotation created: polygon={len(annotation.polygon) if annotation.polygon else 0}, bbox={annotation.bbox}")
            print(f"[DEBUG] Quality metrics: score={annotation.quality_score:.3f}, density={annotation.vertex_density:.2f}")

            # Add to canvas and project - use same annotation object
            self.canvas.annotations.append(annotation)
            self.layer_list.annotations.append(annotation)

            # Save history
            self.canvas.save_history()

            # Update displays
            self.canvas.update()
            self.layer_list.update_list()
            self.layer_list.update_stats()

            image_path = self.image_manager.get_current_image_path()
            self.project_manager.add_annotation(image_path, annotation)

            self.status_label.setText(f"分割完成，置信度: {best_score:.2f}")
        else:
            self.status_label.setText("分割失败")

    def on_box_drawn(self, box: tuple):
        """边界框绘制回调 - SAM2分割"""
        if not self.sam2_engine or not self.sam2_engine.is_loaded:
            self.status_label.setText("SAM2模型未加载")
            return

        x, y, w, h = box
        sam2_box = [x, y, x + w, y + h]

        self.status_label.setText("正在进行分割...")

        masks, scores, _ = self.sam2_engine.predict_from_box(sam2_box)

        if masks is not None:
            best_mask = self.sam2_engine.get_best_mask(masks, scores)
            best_score = float(scores.max()) if scores is not None else 0.0

            polygon = self.sam2_engine.mask_to_polygon(best_mask)
            bbox = self.sam2_engine.mask_to_bbox(best_mask)

            annotation = Annotation(
                class_name=self.current_class,
                mask=best_mask,
                polygon=polygon,
                bbox=bbox,
                confidence=best_score,
                color=self.current_color
            )

            # 计算质量指标
            annotation.calculate_quality_metrics(self.config.get_quality_config())

            self.canvas.annotations.append(annotation)
            self.layer_list.annotations.append(annotation)
            self.canvas.save_history()
            self.canvas.update()
            self.layer_list.update_list()
            self.layer_list.update_stats()

            image_path = self.image_manager.get_current_image_path()
            self.project_manager.add_annotation(image_path, annotation)

            self.status_label.setText(f"分割完成，置信度: {best_score:.2f}")

    def on_polygon_drawn(self, polygon: list):
        """多边形绘制回调"""
        # Calculate bbox from polygon
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]

        annotation = Annotation(
            class_name=self.current_class,
            polygon=polygon,
            bbox=bbox,
            is_manual=True,
            confidence=1.0,  # 手动标注置信度为1
            color=self.current_color
        )

        # 计算质量指标
        annotation.calculate_quality_metrics(self.config.get_quality_config())

        self.canvas.annotations.append(annotation)
        self.layer_list.annotations.append(annotation)
        self.canvas.save_history()
        self.canvas.update()
        self.layer_list.update_list()
        self.layer_list.update_stats()

        image_path = self.image_manager.get_current_image_path()
        self.project_manager.add_annotation(image_path, annotation)

        # Debug: 验证添加后project中的数据
        img_ann = self.project_manager.get_image_annotation(image_path)
        if img_ann:
            print(f"[DEBUG] After adding, project has {len(img_ann.annotations)} annotations")
            for ann in img_ann.annotations:
                print(f"[DEBUG]   - Annotation {ann.id}: polygon={len(ann.polygon) if ann.polygon else 'empty'}")

        self.status_label.setText("多边形标注已添加")

    def on_annotation_selected(self, annotation_id: int):
        """标注选择回调 - 画布选中时同步到列表"""
        self.layer_list.select_annotation(annotation_id)

    def on_annotation_clicked(self, annotation_id: int):
        """标注点击回调 - 同步显示选中标注并居中"""
        # 同步canvas的annotations列表
        self.canvas.annotations = self.layer_list.annotations.copy()
        # 选中标注
        self.canvas.select_annotation(annotation_id)

        # 居中显示选中标注
        self.center_annotation_on_canvas(annotation_id)

        self.canvas.update()
        print(f"Annotation clicked: ID={annotation_id}, canvas has {len(self.canvas.annotations)} annotations")

    def center_annotation_on_canvas(self, annotation_id: int):
        """将选中的标注居中显示"""
        # 找到标注
        annotation = None
        for ann in self.canvas.annotations:
            if ann.id == annotation_id:
                annotation = ann
                break

        if annotation is None or not annotation.polygon:
            return

        # 计算标注polygon的中心点
        xs = [p[0] for p in annotation.polygon]
        ys = [p[1] for p in annotation.polygon]
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)

        # 获取canvas尺寸
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()

        # 计算新的offset使标注中心在canvas中心
        # offset = canvas_center - image_center * scale
        new_offset_x = int(canvas_width / 2 - center_x * self.canvas.scale)
        new_offset_y = int(canvas_height / 2 - center_y * self.canvas.scale)

        self.canvas.offset = QPoint(new_offset_x, new_offset_y)

    def on_annotation_deleted(self, annotation_id: int):
        """标注删除回调 - 同步删除"""
        # Remove from layer_list annotations
        self.layer_list.annotations = [a for a in self.layer_list.annotations if a.id != annotation_id]

        # Sync to canvas
        self.canvas.annotations = self.layer_list.annotations.copy()

        # Clear selection if deleted
        if self.canvas.selected_annotation == annotation_id:
            self.canvas.selected_annotation = None

        # Update displays
        self.layer_list.update_list()
        self.layer_list.update_stats()
        self.canvas.update()

        # Remove from project
        image_path = self.image_manager.get_current_image_path()
        self.project_manager.remove_annotation(image_path, annotation_id)

        self.status_label.setText("标注已删除")
        print(f"Annotation deleted: ID={annotation_id}, remaining: {len(self.canvas.annotations)}")

    def on_annotations_loaded(self, annotations: list):
        """加载标注文件回调 - 同步到canvas和project_manager"""
        self.canvas.annotations = list(annotations)
        self.layer_list.annotations = list(annotations)
        self.canvas.selected_annotation = None
        self.canvas.save_history()
        self.canvas.update()
        self.layer_list.update_list()
        self.layer_list.update_stats()

        # 同步到 project_manager
        image_path = self.image_manager.get_current_image_path()
        if image_path and annotations:
            # 确保项目存在
            if self.project_manager.project is None:
                self.project_manager.create_project("标注项目", "")

            # 获取或创建 image annotation
            img_size = self.image_manager.get_current_image_size()
            img_ann = self.project_manager.get_image_annotation(image_path)
            if img_ann is None:
                img_ann = self.project_manager.add_image_to_project(image_path, img_size)

            if img_ann:
                img_ann.annotations = list(annotations)
                print(f"Loaded {len(annotations)} annotations synced to project_manager for {image_path}")

        self.status_label.setText(f"已加载 {len(annotations)} 个标注")

    def on_class_changed(self, annotation_id: int, class_name: str):
        """类别更改回调"""
        image_path = self.image_manager.get_current_image_path()
        self.project_manager.update_annotation(
            image_path, annotation_id, {"class_name": class_name}
        )
        self.canvas.update()

    def on_label_changed(self, annotation_id: int, label: str):
        """文本标注变更回调"""
        image_path = self.image_manager.get_current_image_path()
        if image_path:
            self.project_manager.update_annotation(
                image_path, annotation_id, {"label": label}
            )
        self.canvas.update()

    def on_canvas_update_requested(self):
        """Canvas更新请求回调"""
        self.canvas.update()

    def on_visibility_changed(self, annotation_id: int, visible: bool):
        """可见性变更回调"""
        image_path = self.image_manager.get_current_image_path()
        self.project_manager.update_annotation(
            image_path, annotation_id, {"visible": visible}
        )
        self.canvas.update()

    def on_annotation_confirmed(self, annotation_id: int):
        """确认标注回调"""
        self.status_label.setText(f"标注已确认: ID {annotation_id}")
        self.canvas.update()

    def on_annotation_adjusted(self, annotation_id: int):
        """微调标注回调 - 进入编辑模式"""
        self.current_tool = "edit"
        self.canvas.set_tool("edit")
        self.canvas.select_annotation(annotation_id)
        self.status_label.setText("进入微调模式，可拖拽顶点调整边界")

    def on_class_changed_tool(self, class_name: str, color: str):
        """工具栏类别更改回调"""
        self.current_class = class_name
        self.current_color = color

    def on_tool_changed(self, tool: str):
        """工具更改回调"""
        self.current_tool = tool
        self.canvas.set_tool(tool)
        self.status_label.setText(f"工具: {tool}")

    def new_project(self):
        """新建项目"""
        if self.project_manager.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "保存",
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.project_manager.create_project("新建项目", "")

    def open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目",
            "",
            "Project Files (*.json *.sam2proj)"
        )

        if file_path:
            project = self.project_manager.load_project(file_path)
            if project:
                self.status_label.setText(f"项目已加载: {project.name}")
            else:
                QMessageBox.warning(self, "错误", "无法加载项目文件")

    def save_project(self):
        """保存项目"""
        if not self.project_manager.project_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存项目",
                "",
                "Project Files (*.json *.sam2proj)"
            )

            if file_path:
                self.project_manager.save_project(file_path)
                self.status_label.setText(f"项目已保存: {file_path}")

        else:
            self.project_manager.save_project()
            self.status_label.setText("项目已保存")

    def export_annotations(self):
        """导出标注"""
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择导出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return

        # Ask for format
        format_dialog = QMessageBox(self)
        format_dialog.setWindowTitle("导出格式")
        format_dialog.setText("选择导出格式:")
        format_dialog.addButton("COCO JSON", QMessageBox.ButtonRole.AcceptRole)
        format_dialog.addButton("VOC XML", QMessageBox.ButtonRole.AcceptRole)
        format_dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)

        format_dialog.exec()

        clicked_button = format_dialog.clickedButton()
        if clicked_button:
            button_text = clicked_button.text()

            if button_text == "COCO JSON":
                self.save_coco_format(output_dir)
            elif button_text == "VOC XML":
                self.save_voc_format(output_dir)

    def save_coco_format(self, output_dir: str = None):
        """保存COCO格式标注"""
        from ..exporters.coco_exporter import COCOExporter

        # Debug: 导出前检查数据
        print("[DEBUG] Before sync - layer_list.annotations:")
        for ann in self.layer_list.annotations:
            print(f"  - ID {ann.id}: polygon={len(ann.polygon) if ann.polygon else 'empty'}")

        # 确保项目存在并同步标注
        self.sync_current_annotations()

        # Debug: 同步后检查数据
        print("[DEBUG] After sync - project_manager data:")
        if self.project_manager.project:
            for img_ann in self.project_manager.project.images:
                print(f"  Image: {img_ann.image_path}")
                for ann in img_ann.annotations:
                    print(f"    - ID {ann.id}: polygon={len(ann.polygon) if ann.polygon else 'empty'}")

        if self.project_manager.project is None or not self.project_manager.project.images:
            QMessageBox.warning(self, "警告", "没有可保存的标注数据")
            return

        if output_dir is None:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "选择COCO导出目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

        if not output_dir:
            return

        # 获取项目名和当前图片名
        project_name = self.project_manager.project.name if self.project_manager.project else "project"
        current_image_path = self.image_manager.get_current_image_path()
        image_name = os.path.splitext(os.path.basename(current_image_path))[0] if current_image_path else "image"

        exporter = COCOExporter(output_dir, project_name=project_name, image_name=image_name)
        if exporter.export(self.project_manager.project):
            self.status_label.setText(f"COCO标注已导出到: {output_dir}")
            self.layer_list.set_file_path(os.path.join(output_dir, os.path.basename(exporter.output_file)))
            QMessageBox.information(self, "成功", f"标注已保存:\n{exporter.output_file}")
        else:
            QMessageBox.warning(self, "错误", "导出失败")

    def save_voc_format(self, output_dir: str = None):
        """保存VOC格式标注"""
        from ..exporters.voc_exporter import VOCExporter

        # 确保项目存在并同步标注
        self.sync_current_annotations()

        if self.project_manager.project is None or not self.project_manager.project.images:
            QMessageBox.warning(self, "警告", "没有可保存的标注数据")
            return

        if output_dir is None:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "选择VOC导出目录",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

        if not output_dir:
            return

        # 获取项目名
        project_name = self.project_manager.project.name if self.project_manager.project else "project"

        exporter = VOCExporter(output_dir, project_name=project_name)
        if exporter.export(self.project_manager.project):
            self.status_label.setText(f"VOC标注已导出到: {output_dir}")
            QMessageBox.information(self, "成功", f"标注已保存:\n{output_dir}/Annotations/")
        else:
            QMessageBox.warning(self, "错误", "导出失败")

    def sync_current_annotations(self):
        """同步当前标注到项目"""
        image_path = self.image_manager.get_current_image_path()
        if not image_path:
            return

        # 确保项目存在
        if self.project_manager.project is None:
            self.project_manager.create_project("标注项目", "")

        # 获取当前标注列表
        annotations = self.layer_list.get_all_annotations()
        print(f"Syncing {len(annotations)} annotations for image: {image_path}")

        # Debug: 检查每个标注的polygon
        for ann in annotations:
            print(f"Annotation {ann.id}: polygon={ann.polygon[:3] if ann.polygon else 'empty'}, bbox={ann.bbox}")

        # 更新或创建image annotation
        img_ann = self.project_manager.get_image_annotation(image_path)
        if img_ann:
            img_ann.annotations = annotations
        else:
            img_size = self.image_manager.get_current_image_size()
            img_ann = self.project_manager.add_image_to_project(image_path, img_size)
            if img_ann:
                img_ann.annotations = annotations

    def delete_selected_annotation(self):
        """删除选中的标注"""
        selected = self.layer_list.get_selected_annotation()
        if selected:
            self.on_annotation_deleted(selected)

    def clear_all_annotations(self):
        """清除所有标注"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除所有标注吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_annotations()
            self.layer_list.clear_annotations()
            image_path = self.image_manager.get_current_image_path()
            if self.project_manager.project:
                img_ann = self.project_manager.get_image_annotation(image_path)
                if img_ann:
                    img_ann.clear_annotations()
            self.status_label.setText("所有标注已清除")

    def undo(self):
        """撤销"""
        self.canvas.undo()
        self.status_label.setText("已撤销")

    def redo(self):
        """重做"""
        self.canvas.redo()
        self.status_label.setText("已重做")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "SAM2 Annotation Tool\n\n"
            "基于SAM2模型的图片标注工具\n"
            "支持点点击分割、边界框分割、多边形标注\n"
            "可导出VOC XML和COCO JSON格式\n\n"
            "Version: 1.0.0"
        )

    def closeEvent(self, event):
        """关闭事件"""
        if self.project_manager.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "保存",
                "有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_project()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主入口"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())