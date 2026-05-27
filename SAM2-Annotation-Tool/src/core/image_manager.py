"""Image Manager for handling image files"""

import os
import glob
from typing import List, Optional, Tuple
import numpy as np
import cv2
from pathlib import Path


class ImageManager:
    """图像管理器"""

    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']

    def __init__(self):
        self.images: List[str] = []
        self.current_index: int = -1
        self.current_image: Optional[np.ndarray] = None
        self.image_dir: str = ""

    def load_images_from_dir(self, directory: str) -> List[str]:
        """从目录加载所有图像"""
        self.image_dir = directory
        self.images = []

        # Windows文件系统不区分大小写，只搜索小写扩展名避免重复
        for ext in self.SUPPORTED_FORMATS:
            pattern = os.path.join(directory, f'*{ext}')
            self.images.extend(glob.glob(pattern))

        # 去重并排序
        self.images = list(set(self.images))
        self.images.sort()

        self.current_index = -1 if not self.images else 0

        if self.images:
            self.load_current_image()

        return self.images

    def load_current_image(self) -> Optional[np.ndarray]:
        """加载当前图像"""
        if self.current_index < 0 or self.current_index >= len(self.images):
            print(f"Warning: Invalid index {self.current_index}, images count: {len(self.images)}")
            return None

        try:
            image_path = self.images[self.current_index]
            print(f"Loading image from: {image_path}")

            # Use np.fromfile to handle Chinese paths on Windows
            image_data = np.fromfile(image_path, dtype=np.uint8)
            self.current_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            if self.current_image is None:
                print(f"Error: cv2.imdecode failed for {image_path}")
            else:
                print(f"Image loaded successfully: shape {self.current_image.shape}")

            return self.current_image

        except Exception as e:
            print(f"Failed to load image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_image(self, index: int) -> Optional[np.ndarray]:
        """加载指定索引的图像"""
        if index < 0 or index >= len(self.images):
            return None

        self.current_index = index
        return self.load_current_image()

    def get_current_image_path(self) -> Optional[str]:
        """获取当前图像路径"""
        if self.current_index < 0 or self.current_index >= len(self.images):
            return None
        return self.images[self.current_index]

    def get_current_image_size(self) -> Tuple[int, int]:
        """获取当前图像尺寸"""
        if self.current_image is None:
            return (0, 0)
        return (self.current_image.shape[1], self.current_image.shape[0])

    def next_image(self) -> Optional[np.ndarray]:
        """下一张图像"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            return self.load_current_image()
        return None

    def prev_image(self) -> Optional[np.ndarray]:
        """上一张图像"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.load_current_image()
        return None

    def get_image_count(self) -> int:
        """获取图像总数"""
        return len(self.images)

    def get_index_by_path(self, path: str) -> int:
        """通过路径获取索引"""
        try:
            return self.images.index(path)
        except ValueError:
            return -1

    def clear(self):
        """清除所有图像"""
        self.images = []
        self.current_index = -1
        self.current_image = None
        self.image_dir = ""