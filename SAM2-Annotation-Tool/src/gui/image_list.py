"""Image List Widget"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QHBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QImage
import os
import numpy as np
import cv2
from typing import List


class ImageList(QWidget):
    """图片列表控件"""

    image_selected = pyqtSignal(str)  # Image path

    def __init__(self, parent=None):
        super().__init__(parent)

        self.images: List[str] = []
        self.current_index: int = -1

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("图片列表")
        header.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.prev_btn = QPushButton("上一张")
        self.prev_btn.clicked.connect(self.prev_image)
        button_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一张")
        self.next_btn.clicked.connect(self.next_image)
        button_layout.addWidget(self.next_btn)

        layout.addLayout(button_layout)

        # Count label
        self.count_label = QLabel("共 0 张图片")
        self.count_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.count_label)

    def set_images(self, images: List[str]):
        """设置图片列表"""
        self.images = images
        self.current_index = 0 if images else -1
        self.update_list()

    def add_images(self, images: List[str]):
        """添加图片到列表（不清空现有列表）"""
        for img in images:
            if img not in self.images:
                self.images.append(img)
        self.update_list()

    def update_list(self):
        """更新列表"""
        self.list_widget.clear()

        for i, image_path in enumerate(self.images):
            item = QListWidgetItem()

            # Get filename
            filename = os.path.basename(image_path)
            item.setText(f"{i + 1}. {filename}")
            item.setData(Qt.ItemDataRole.UserRole, image_path)

            # Try to load thumbnail (support Chinese path)
            try:
                thumbnail = self.load_thumbnail(image_path)
                if thumbnail:
                    item.setIcon(QIcon(thumbnail))
            except:
                pass

            self.list_widget.addItem(item)

        self.count_label.setText(f"共 {len(self.images)} 张图片")

        if self.images:
            self.list_widget.setCurrentRow(self.current_index if self.current_index >= 0 else 0)

    def load_thumbnail(self, image_path: str) -> QPixmap:
        """加载缩略图（支持中文路径）"""
        try:
            # Use np.fromfile for Chinese path support
            image_data = np.fromfile(image_path, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            if image is None:
                return None

            # Convert to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Resize to thumbnail
            h, w = image.shape[:2]
            scale = 64 / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            thumbnail = cv2.resize(image, (new_w, new_h))

            # Convert to QPixmap
            qimage = QImage(thumbnail.data, new_w, new_h, 3 * new_w, QImage.Format.Format_RGB888)
            return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"Failed to load thumbnail: {e}")
            return None

    def on_item_clicked(self, item: QListWidgetItem):
        """项点击"""
        image_path = item.data(Qt.ItemDataRole.UserRole)
        try:
            self.current_index = self.images.index(image_path)
        except ValueError:
            self.current_index = 0
        self.image_selected.emit(image_path)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """项双击"""
        self.on_item_clicked(item)

    def prev_image(self):
        """上一张"""
        if self.current_index > 0:
            self.current_index -= 1
            self.list_widget.setCurrentRow(self.current_index)
            image_path = self.images[self.current_index]
            self.image_selected.emit(image_path)

    def next_image(self):
        """下一张"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.list_widget.setCurrentRow(self.current_index)
            image_path = self.images[self.current_index]
            self.image_selected.emit(image_path)

    def get_current_image(self) -> str:
        """获取当前图片路径"""
        if self.current_index >= 0 and self.current_index < len(self.images):
            return self.images[self.current_index]
        return ""

    def clear(self):
        """清空图片列表"""
        self.images.clear()
        self.list_widget.clear()
        self.current_index = -1
        self.count_label.setText("共 0 张图片")