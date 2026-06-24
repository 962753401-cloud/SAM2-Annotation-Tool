"""Canvas Widget for Image Annotation"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QBrush,
    QPainterPath, QFont, QPolygonF, QCursor
)
from typing import List, Optional, Tuple, Dict
from ..core.annotation_data import Annotation


class CanvasWidget(QWidget):
    """画布控件 - 核心交互区域"""

    # Signals
    point_clicked = pyqtSignal(tuple)  # (x, y)
    box_drawn = pyqtSignal(tuple)      # (x, y, w, h)
    polygon_drawn = pyqtSignal(list)   # [[x, y], [x, y], ...]
    annotation_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Image state
        self.image: Optional[np.ndarray] = None
        self.pixmap: Optional[QPixmap] = None
        self.annotations: List[Annotation] = []

        # Display state
        self.scale: float = 1.0
        self.offset: QPoint = QPoint(0, 0)
        self.min_scale: float = 0.1
        self.max_scale: float = 10.0

        # Interaction state
        self.current_tool: str = "point"
        self.drawing_box: bool = False
        self.drawing_polygon: bool = False
        self.box_start: Optional[QPoint] = None
        self.box_end: Optional[QPoint] = None
        self.polygon_points: List[QPoint] = []
        self.selected_annotation: Optional[int] = None
        self.hover_annotation: Optional[int] = None

        # Vertex dragging state for edit mode
        self.dragging_vertex: bool = False
        self.drag_annotation_id: Optional[int] = None
        self.drag_vertex_index: int = -1
        self.vertex_radius: int = 8  # 顶点检测半径

        # Context menu state for edit mode
        self.context_menu_pos: Optional[QPointF] = None
        self.nearest_vertex_index: int = 0
        self.nearest_edge_index: int = 0

        # History for undo/redo
        self.history: List[List[Annotation]] = []
        self.history_index: int = -1

        # Display settings
        self.mask_opacity: float = 0.5
        self.show_masks: bool = True
        self.show_polygons: bool = True
        self.show_bbox: bool = True

        # Mouse tracking
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Enable scroll
        self.setMinimumSize(400, 300)

    def set_image(self, image: np.ndarray):
        """设置图像"""
        if image is None:
            return

        # Ensure image is contiguous array
        image = np.ascontiguousarray(image)

        self.image = image
        self.annotations.clear()
        self.selected_annotation = None
        self.history.clear()
        self.history_index = -1

        # Convert numpy to QPixmap
        h, w = image.shape[:2]
        ch = 1 if len(image.shape) == 2 else image.shape[2]

        if ch == 3:
            # BGR format (cv2.imread returns BGR)
            bytes_per_line = 3 * w
            qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        elif ch == 4:
            # BGRA format
            bytes_per_line = 4 * w
            qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        else:
            # Grayscale
            bytes_per_line = w
            qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)

        self.pixmap = QPixmap.fromImage(qimage)

        if self.pixmap.isNull():
            print(f"Warning: Failed to create pixmap from image (size: {w}x{h})")
            self.pixmap = None
            return

        # Fit to window
        self.fit_to_window()
        self.save_history()
        self.update()
        print(f"Image loaded: {w}x{h}")

    def set_annotations(self, annotations: List[Annotation]):
        """设置标注列表"""
        # 直接引用而非复制，保持与layer_list同步
        self.annotations = list(annotations)  # 创建新列表但保持引用相同对象
        self.selected_annotation = None
        self.update()
        print(f"Canvas: Set {len(self.annotations)} annotations")

    def add_annotation(self, annotation: Annotation):
        """添加标注"""
        self.annotations.append(annotation)
        self.save_history()
        self.update()
        print(f"Canvas: Added annotation ID={annotation.id}, polygon points={len(annotation.polygon)}")

    def remove_annotation(self, annotation_id: int):
        """删除标注"""
        self.annotations = [a for a in self.annotations if a.id != annotation_id]
        self.save_history()
        self.update()

    def clear_annotations(self):
        """清除所有标注"""
        self.annotations.clear()
        self.selected_annotation = None
        self.save_history()
        self.update()

    def select_annotation(self, annotation_id: int):
        """选择标注"""
        self.selected_annotation = annotation_id
        self.update()

    def update_annotation_color(self, annotation_id: int):
        """更新标注颜色"""
        self.update()

    def set_tool(self, tool: str):
        """设置当前工具"""
        self.current_tool = tool
        self.drawing_box = False
        self.drawing_polygon = False
        self.polygon_points.clear()
        self.box_start = None
        self.box_end = None

        if tool == "polygon":
            self.drawing_polygon = True

    def save_history(self):
        """保存历史"""
        # Remove future history if we're not at the end
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Save current state (deep copy)
        import copy
        self.history.append([copy.deepcopy(a) for a in self.annotations])
        self.history_index = len(self.history) - 1

        # Limit history size
        if len(self.history) > 50:
            self.history = self.history[-50:]
            self.history_index = len(self.history) - 1

    def undo(self):
        """撤销"""
        if self.history_index > 0:
            self.history_index -= 1
            import copy
            self.annotations = copy.deepcopy(self.history[self.history_index])
            self.update()

    def redo(self):
        """重做"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            import copy
            self.annotations = copy.deepcopy(self.history[self.history_index])
            self.update()

    def zoom_in(self):
        """放大"""
        self.scale = min(self.max_scale, self.scale * 1.2)
        self.update()

    def zoom_out(self):
        """缩小"""
        self.scale = max(self.min_scale, self.scale / 1.2)
        self.update()

    def fit_to_window(self):
        """适应窗口"""
        if self.pixmap is None or self.pixmap.isNull():
            return

        widget_size = self.size()
        pixmap_size = self.pixmap.size()

        # Handle zero size
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            self.scale = 1.0
            return

        if pixmap_size.width() <= 0 or pixmap_size.height() <= 0:
            return

        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()

        self.scale = min(scale_x, scale_y) * 0.9
        self.scale = max(0.01, self.scale)  # Ensure minimum scale

        self.offset = QPoint(
            int((widget_size.width() - pixmap_size.width() * self.scale) // 2),
            int((widget_size.height() - pixmap_size.height() * self.scale) // 2)
        )
        self.update()
        print(f"Fit to window: scale={self.scale:.2f}, offset={self.offset}")

    def screen_to_image(self, point: QPoint) -> Tuple[int, int]:
        """屏幕坐标转图像坐标"""
        if self.pixmap is None:
            return (0, 0)

        x = int((point.x() - self.offset.x()) / self.scale)
        y = int((point.y() - self.offset.y()) / self.scale)

        # Clamp to image bounds
        x = max(0, min(x, self.pixmap.width() - 1))
        y = max(0, min(y, self.pixmap.height() - 1))

        return (x, y)

    def image_to_screen(self, point: Tuple[int, int]) -> QPoint:
        """图像坐标转屏幕坐标"""
        return QPoint(
            int(point[0] * self.scale + self.offset.x()),
            int(point[1] * self.scale + self.offset.y())
        )

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw background
            painter.fillRect(self.rect(), QColor(42, 42, 42))

            if self.pixmap is None or self.pixmap.isNull():
                # Show placeholder
                painter.setPen(QPen(QColor(100, 100, 100)))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请打开图片")
                return

            # Draw image - scale pixmap properly
            target_width = int(self.pixmap.width() * self.scale)
            target_height = int(self.pixmap.height() * self.scale)

            if target_width > 0 and target_height > 0:
                scaled_pixmap = self.pixmap.scaled(
                    target_width,
                    target_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.drawPixmap(self.offset, scaled_pixmap)

            # Draw annotations - show all annotations with outlines
            for annotation in self.annotations:
                if not annotation.visible:
                    continue

                is_selected = annotation.id == self.selected_annotation

                # Color: red for unconfirmed, green for confirmed
                if annotation.label:
                    outline_color = QColor(0, 255, 0)  # Green for confirmed
                else:
                    outline_color = QColor(255, 0, 0)  # Red for unconfirmed

                # Selected uses thicker line and yellow highlight
                if is_selected:
                    outline_color = QColor(255, 255, 0)  # Yellow for selected

                # Draw polygon outline only (no fill)
                if annotation.polygon and len(annotation.polygon) >= 3:
                    self.draw_polygon_outline(painter, annotation.polygon, outline_color, is_selected)

                # Draw bbox
                if annotation.bbox and len(annotation.bbox) >= 4:
                    self.draw_bbox(painter, annotation.bbox, outline_color, is_selected)

                # Draw label text if exists
                if annotation.label:
                    self.draw_label_text(painter, annotation.polygon, annotation.label)

            # Draw current drawing
            if self.drawing_box and self.box_start and self.box_end:
                self.draw_temp_box(painter)

            if self.drawing_polygon and self.polygon_points:
                self.draw_temp_polygon(painter)

        except Exception as e:
            print(f"[ERROR] paintEvent failed: {e}")
            import traceback
            traceback.print_exc()
            # 绘制错误提示
            painter.fillRect(self.rect(), QColor(42, 42, 42))
            painter.setPen(QPen(QColor(255, 0, 0)))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"绘制错误: {e}")
        finally:
            painter.end()

    def draw_polygon_outline(self, painter: QPainter, polygon: List[List[int]], color: QColor, is_selected: bool):
        """绘制多边形轮廓（只描边，不填充）"""
        points = [self.image_to_screen(p) for p in polygon]

        # No fill
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Red outline, thicker when selected
        pen_width = 3 if is_selected else 2
        painter.setPen(QPen(color, pen_width))

        # Draw outline
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            painter.drawLine(points[i], points[next_i])

        # Draw vertices for editing when selected
        if is_selected:
            painter.setPen(QPen(QColor(255, 255, 0), 2))  # Yellow vertices
            for point in points:
                painter.drawEllipse(point, 5, 5)

    def draw_label_text(self, painter: QPainter, polygon: List[List[int]], label: str):
        """绘制标注文本"""
        if not polygon or not label:
            return

        # Calculate center position
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)

        screen_center = self.image_to_screen((int(center_x), int(center_y)))

        # Draw text background
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))

        # Calculate text rect
        font = QFont("Arial", 12)
        painter.setFont(font)

        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(label)
        text_height = fm.height()

        text_rect = QRectF(
            screen_center.x() - text_width / 2 - 5,
            screen_center.y() - text_height / 2 - 2,
            text_width + 10,
            text_height + 4
        )
        painter.drawRect(text_rect)

        # Draw text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(
            int(screen_center.x() - text_width / 2),
            int(screen_center.y() + text_height / 4),
            label
        )

    def draw_bbox(self, painter: QPainter, bbox: List[int], color: QColor, is_selected: bool):
        """绘制边界框"""
        x, y, w, h = bbox
        screen_rect = QRectF(
            self.image_to_screen((x, y)).x(),
            self.image_to_screen((x, y)).y(),
            w * self.scale,
            h * self.scale
        )

        pen_width = 2 if is_selected else 1
        painter.setPen(QPen(color, pen_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(screen_rect)

    def draw_temp_box(self, painter: QPainter):
        """绘制临时边界框"""
        painter.setPen(QPen(QColor(255, 255, 0), 2))
        painter.setBrush(QBrush(QColor(255, 255, 0, 50)))

        rect = QRectF(self.box_start, self.box_end)
        painter.drawRect(rect)

    def draw_temp_polygon(self, painter: QPainter):
        """绘制临时多边形"""
        painter.setPen(QPen(QColor(255, 255, 0), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw lines
        for i in range(len(self.polygon_points) - 1):
            painter.drawLine(self.polygon_points[i], self.polygon_points[i + 1])

        # Draw points
        for point in self.polygon_points:
            painter.drawEllipse(point, 4, 4)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self.pixmap is None:
            return

        pos = event.position()

        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == "point":
                # Point click - SAM2 segmentation
                image_pos = self.screen_to_image(pos)
                self.point_clicked.emit(image_pos)

            elif self.current_tool == "box":
                # Start drawing box
                self.drawing_box = True
                self.box_start = pos
                self.box_end = pos

            elif self.current_tool == "polygon":
                # Add polygon point
                self.polygon_points.append(pos)
                self.update()

            elif self.current_tool == "edit":
                # First check if clicking on a vertex of the selected annotation
                if self.selected_annotation is not None:
                    selected_ann = None
                    for ann in self.annotations:
                        if ann.id == self.selected_annotation:
                            selected_ann = ann
                            break

                    if selected_ann and selected_ann.polygon:
                        image_pos = self.screen_to_image(pos)
                        # Check if clicking near any vertex
                        for i, vertex in enumerate(selected_ann.polygon):
                            vertex_screen = self.image_to_screen(vertex)
                            dist = ((vertex_screen.x() - pos.x()) ** 2 + (vertex_screen.y() - pos.y()) ** 2) ** 0.5
                            if dist <= self.vertex_radius:
                                # Start dragging this vertex
                                self.dragging_vertex = True
                                self.drag_annotation_id = self.selected_annotation
                                self.drag_vertex_index = i
                                self.update()
                                return

                # If not clicking on vertex, select annotation
                image_pos = self.screen_to_image(pos)
                for ann in reversed(self.annotations):
                    if ann.contains_point(image_pos[0], image_pos[1]):
                        self.selected_annotation = ann.id
                        self.annotation_selected.emit(ann.id)
                        self.update()
                        return

        elif event.button() == Qt.MouseButton.RightButton:
            if self.current_tool == "polygon" and len(self.polygon_points) >= 3:
                # Complete polygon
                polygon = [self.screen_to_image(p) for p in self.polygon_points]
                self.polygon_drawn.emit(polygon)
                self.polygon_points.clear()
                self.update()

            elif self.current_tool == "edit" and self.selected_annotation is not None:
                # Show context menu for adding/deleting vertices
                self.show_edit_context_menu(pos)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.pixmap is None:
            return

        pos = event.position()

        # Handle vertex dragging
        if self.dragging_vertex and self.drag_annotation_id is not None:
            image_pos = self.screen_to_image(pos)
            # Find the annotation and update the vertex
            for ann in self.annotations:
                if ann.id == self.drag_annotation_id:
                    if ann.polygon and self.drag_vertex_index < len(ann.polygon):
                        ann.polygon[self.drag_vertex_index] = list(image_pos)
                        # Also update bbox
                        xs = [p[0] for p in ann.polygon]
                        ys = [p[1] for p in ann.polygon]
                        ann.bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
                        self.update()
                    break
            return

        if self.drawing_box:
            self.box_end = pos
            self.update()

        # Hover detection
        if self.current_tool == "edit":
            image_pos = self.screen_to_image(pos)
            hover_id = None
            for ann in reversed(self.annotations):
                if ann.contains_point(image_pos[0], image_pos[1]):
                    hover_id = ann.id
                    break

            if hover_id != self.hover_annotation:
                self.hover_annotation = hover_id
                self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle vertex drag completion
            if self.dragging_vertex:
                self.dragging_vertex = False
                self.drag_annotation_id = None
                self.drag_vertex_index = -1
                self.save_history()  # Save state after vertex adjustment
                self.update()
                return

            # Handle box drawing completion
            if self.drawing_box:
                self.drawing_box = False

                if self.box_start and self.box_end:
                    # Calculate box in image coordinates
                    start = self.screen_to_image(self.box_start)
                    end = self.screen_to_image(self.box_end)

                    x = min(start[0], end[0])
                    y = min(start[1], end[1])
                    w = abs(end[0] - start[0])
                    h = abs(end[1] - start[1])

                    if w > 5 and h > 5:  # Minimum size
                        self.box_drawn.emit((x, y, w, h))

            self.box_start = None
            self.box_end = None
            self.update()

    def wheelEvent(self, event):
        """滚轮事件 - 缩放"""
        if self.pixmap is None:
            return

        delta = event.angleDelta().y()

        old_scale = self.scale
        if delta > 0:
            self.scale = min(self.max_scale, self.scale * 1.1)
        else:
            self.scale = max(self.min_scale, self.scale / 1.1)

        # Center zoom on mouse position
        mouse_pos = event.position()
        self.offset = QPoint(
            int(mouse_pos.x() - (mouse_pos.x() - self.offset.x()) * (self.scale / old_scale)),
            int(mouse_pos.y() - (mouse_pos.y() - self.offset.y()) * (self.scale / old_scale))
        )

        self.update()

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key.Key_Escape:
            # Cancel current drawing
            self.drawing_box = False
            self.drawing_polygon = False
            self.polygon_points.clear()
            self.box_start = None
            self.box_end = None
            self.selected_annotation = None
            self.update()

        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if self.current_tool == "polygon" and len(self.polygon_points) >= 3:
                polygon = [self.screen_to_image(p) for p in self.polygon_points]
                self.polygon_drawn.emit(polygon)
                self.polygon_points.clear()
                self.update()

    def show_edit_context_menu(self, pos):
        """显示编辑模式下的右键菜单"""
        # Find the selected annotation
        selected_ann = None
        for ann in self.annotations:
            if ann.id == self.selected_annotation:
                selected_ann = ann
                break

        if selected_ann is None or not selected_ann.polygon:
            return

        # Store mouse position for later use
        self.context_menu_pos = pos
        image_pos = self.screen_to_image(pos)

        # Find nearest vertex index
        self.nearest_vertex_index = self.find_nearest_vertex(image_pos, selected_ann.polygon)

        # Find nearest edge for adding vertex
        self.nearest_edge_index = self.find_nearest_edge(image_pos, selected_ann.polygon)

        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #3a3a3a; color: #ffffff; }")

        # Add vertex action
        add_action = menu.addAction("在此处添加顶点")
        add_action.setToolTip("在最近的边上添加一个新顶点")

        # Delete vertex action (only if more than 3 vertices)
        if len(selected_ann.polygon) > 3:
            delete_action = menu.addAction("删除最近顶点")
            delete_action.setToolTip(f"删除顶点 #{self.nearest_vertex_index + 1}")

        menu.addSeparator()

        cancel_action = menu.addAction("取消")

        # Show menu and handle action
        action = menu.exec(QCursor.pos())

        if action == add_action:
            self.add_vertex_to_selected()
        elif len(selected_ann.polygon) > 3 and action == delete_action:
            self.delete_vertex_from_selected()
        elif action == cancel_action:
            pass  # Just close menu

    def find_nearest_vertex(self, point: Tuple[int, int], polygon: List[List[int]]) -> int:
        """找到最近的顶点索引"""
        min_dist = float('inf')
        nearest_idx = 0

        for i, vertex in enumerate(polygon):
            dist = (vertex[0] - point[0]) ** 2 + (vertex[1] - point[1]) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

        return nearest_idx

    def find_nearest_edge(self, point: Tuple[int, int], polygon: List[List[int]]) -> int:
        """找到最近的边索引（用于添加顶点）"""
        min_dist = float('inf')
        nearest_idx = 0

        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]

            # Calculate distance from point to line segment
            dist = self.point_to_segment_distance(point, p1, p2)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

        return nearest_idx

    def point_to_segment_distance(self, point: Tuple[int, int], p1: List[int], p2: List[int]) -> float:
        """计算点到线段的距离"""
        import math

        x, y = point
        x1, y1 = p1
        x2, y2 = p2

        # Line segment length squared
        seg_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2

        if seg_len_sq == 0:
            # p1 == p2
            return math.sqrt((x - x1) ** 2 + (y - y1) ** 2)

        # Project point onto line
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / seg_len_sq))

        # Projection point
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        return math.sqrt((x - proj_x) ** 2 + (y - proj_y) ** 2)

    def add_vertex_to_selected(self):
        """在选中标注的最近边上添加顶点"""
        selected_ann = None
        for ann in self.annotations:
            if ann.id == self.selected_annotation:
                selected_ann = ann
                break

        if selected_ann is None or not selected_ann.polygon:
            return

        # Get position to add vertex
        image_pos = self.screen_to_image(self.context_menu_pos)

        # Insert vertex at nearest edge
        edge_idx = self.nearest_edge_index
        insert_idx = edge_idx + 1  # Insert after the first vertex of the edge

        selected_ann.polygon.insert(insert_idx, list(image_pos))

        # Update bbox
        xs = [p[0] for p in selected_ann.polygon]
        ys = [p[1] for p in selected_ann.polygon]
        selected_ann.bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]

        self.save_history()
        self.update()

    def delete_vertex_from_selected(self):
        """删除选中标注的最近顶点"""
        selected_ann = None
        for ann in self.annotations:
            if ann.id == self.selected_annotation:
                selected_ann = ann
                break

        if selected_ann is None or not selected_ann.polygon:
            return

        if len(selected_ann.polygon) <= 3:
            return  # Cannot delete if only 3 vertices

        # Delete nearest vertex
        vertex_idx = self.nearest_vertex_index
        selected_ann.polygon.pop(vertex_idx)

        # Update bbox
        xs = [p[0] for p in selected_ann.polygon]
        ys = [p[1] for p in selected_ann.polygon]
        selected_ann.bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]

        self.save_history()
        self.update()