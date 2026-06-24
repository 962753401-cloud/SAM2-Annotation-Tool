"""Image Utilities"""

import os
import numpy as np
import cv2
from PIL import Image
from typing import Tuple, Optional, List
from pathlib import Path


class ImageUtils:
    """图像处理工具"""

    @staticmethod
    def load_image(path: str) -> Optional[np.ndarray]:
        """加载图像（支持中文路径）"""
        try:
            # Use np.fromfile to handle Chinese paths on Windows
            image_data = np.fromfile(path, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"Failed to load image: {e}")
            return None

    @staticmethod
    def save_image(path: str, image: np.ndarray) -> bool:
        """保存图像（支持中文路径）"""
        try:
            # Use imencode and tofile to handle Chinese paths on Windows
            ext = os.path.splitext(path)[1]
            encoded = cv2.imencode(ext, image)
            encoded[1].tofile(path)
            return True
        except Exception as e:
            print(f"Failed to save image: {e}")
            return False

    @staticmethod
    def resize_image(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """调整图像大小"""
        return cv2.resize(image, size)

    @staticmethod
    def get_image_size(path: str) -> Tuple[int, int]:
        """获取图像尺寸"""
        image = Image.open(path)
        return image.size  # (width, height)

    @staticmethod
    def convert_to_rgb(image: np.ndarray) -> np.ndarray:
        """转换为RGB"""
        if image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    @staticmethod
    def convert_to_bgr(image: np.ndarray) -> np.ndarray:
        """转换为BGR"""
        if image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    @staticmethod
    def create_mask_image(mask: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """创建彩色掩码图像"""
        h, w = mask.shape[:2]
        colored_mask = np.zeros((h, w, 3), dtype=np.uint8)
        colored_mask[mask > 0.5] = color
        return colored_mask

    @staticmethod
    def blend_image_and_mask(image: np.ndarray, mask: np.ndarray, alpha: float = 0.5, color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """混合图像和掩码"""
        colored_mask = ImageUtils.create_mask_image(mask, color)
        blended = cv2.addWeighted(image, 1 - alpha, colored_mask, alpha, 0)
        return blended

    @staticmethod
    def draw_polygon(image: np.ndarray, polygon: List[List[int]], color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """在图像上绘制多边形"""
        pts = np.array(polygon, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, color, thickness)
        return image

    @staticmethod
    def draw_bbox(image: np.ndarray, bbox: List[int], color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """在图像上绘制边界框"""
        x, y, w, h = bbox
        cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)
        return image

    @staticmethod
    def draw_point(image: np.ndarray, point: Tuple[int, int], color: Tuple[int, int, int] = (255, 0, 0), radius: int = 5) -> np.ndarray:
        """在图像上绘制点"""
        cv2.circle(image, point, radius, color, -1)
        return image

    @staticmethod
    def save_mask_as_png(mask: np.ndarray, path: str) -> bool:
        """保存掩码为PNG图像（支持中文路径）"""
        try:
            binary_mask = (mask > 0.5).astype(np.uint8) * 255
            encoded = cv2.imencode('.png', binary_mask)
            encoded[1].tofile(path)
            return True
        except Exception as e:
            print(f"Failed to save mask: {e}")
            return False