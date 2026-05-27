"""Annotation Data Models"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import json
import uuid
import math


@dataclass
class Annotation:
    """单个标注对象"""
    id: int = field(default_factory=lambda: int(uuid.uuid4().int % 1000000))
    class_name: str = "object"
    class_id: int = 0
    label: str = ""  # 文本标注内容
    mask: Optional[np.ndarray] = None
    polygon: List[List[int]] = field(default_factory=list)
    bbox: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    confidence: float = 0.0
    is_manual: bool = False  # True for manually drawn polygons
    color: str = "#ff0000"  # 默认红色描边
    visible: bool = True
    locked: bool = False

    # 新增质量评估字段
    quality_score: float = 0.0       # 综合质量评分 (0-1)
    boundary_smoothness: float = 0.0 # 边界平滑度 (0-1)
    vertex_count: int = 0            # 顶点数量
    vertex_density: float = 0.0      # 顶点密度（每100px边长的顶点数）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "class_name": self.class_name,
            "class_id": self.class_id,
            "label": self.label,
            "polygon": self.polygon,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "is_manual": self.is_manual,
            "color": self.color,
            "visible": self.visible,
            "locked": self.locked,
            # 新增质量指标字段
            "quality_score": self.quality_score,
            "boundary_smoothness": self.boundary_smoothness,
            "vertex_count": self.vertex_count,
            "vertex_density": self.vertex_density
        }

    def from_dict(self, data: Dict[str, Any]) -> 'Annotation':
        """从字典创建/更新 - 只更新提供的字段，保留其他字段不变"""
        if "id" in data:
            self.id = data["id"]
        if "class_name" in data:
            self.class_name = data["class_name"]
        if "class_id" in data:
            self.class_id = data["class_id"]
        if "label" in data:
            self.label = data["label"]
        if "polygon" in data:
            self.polygon = data["polygon"]
        if "bbox" in data:
            self.bbox = data["bbox"]
        if "confidence" in data:
            self.confidence = data["confidence"]
        if "is_manual" in data:
            self.is_manual = data["is_manual"]
        if "color" in data:
            self.color = data["color"]
        if "visible" in data:
            self.visible = data["visible"]
        if "locked" in data:
            self.locked = data["locked"]
        # 新增字段（兼容旧数据，使用默认值）
        self.quality_score = data.get("quality_score", 0.0)
        self.boundary_smoothness = data.get("boundary_smoothness", 0.0)
        self.vertex_count = data.get("vertex_count", len(self.polygon) if self.polygon else 0)
        self.vertex_density = data.get("vertex_density", 0.0)
        return self

    def get_area(self) -> int:
        """计算标注面积"""
        try:
            if self.mask is not None:
                return int(np.sum(self.mask > 0.5))

            if self.polygon:
                # Shoelace formula for polygon area
                n = len(self.polygon)
                if n < 3:
                    return 0

                area = 0
                for i in range(n):
                    j = (i + 1) % n
                    # 安全检查：确保每个点都有至少2个坐标
                    if len(self.polygon[i]) >= 2 and len(self.polygon[j]) >= 2:
                        area += self.polygon[i][0] * self.polygon[j][1]
                        area -= self.polygon[j][0] * self.polygon[i][1]

                return abs(area) // 2

            # Use bbox area
            if len(self.bbox) >= 4:
                return self.bbox[2] * self.bbox[3]
            return 0
        except Exception:
            return 0

    def calculate_quality_metrics(self, config: Dict[str, Any] = None) -> Dict[str, float]:
        """计算分割质量指标

        Args:
            config: 质量评估配置，包含min_vertex_density等参数

        Returns:
            包含各项质量指标的字典
        """
        metrics = {}
        config = config or {}
        min_density = config.get('min_vertex_density', 5)

        # 顶点数量
        self.vertex_count = len(self.polygon) if self.polygon else 0
        metrics['vertex_count'] = self.vertex_count

        # 计算周长
        perimeter = self._calculate_perimeter()
        metrics['perimeter'] = perimeter

        # 顶点密度（修正公式：确保分母不为0且有上限）
        if perimeter > 0 and self.vertex_count > 0:
            # 使用100px作为基准单位，密度上限设为20
            self.vertex_density = min(20.0, self.vertex_count / (perimeter / 100))
        else:
            self.vertex_density = 0
        metrics['vertex_density'] = self.vertex_density

        # 边界平滑度（修正公式：只对非矩形多边形有意义）
        if self.polygon and len(self.polygon) >= 4:
            angle_changes = self._calculate_angle_changes()
            if len(angle_changes) > 0:
                std_angles = np.std(angle_changes)
                # 矩形（4个90度角）的std可能为0，给一个基础分数
                if self.vertex_count <= 5:
                    # 简单形状（矩形/三角形）默认高分
                    self.boundary_smoothness = 0.85
                else:
                    # 复杂形状：std越大越不平滑
                    self.boundary_smoothness = max(0.0, min(1.0, 1.0 - std_angles / 90.0))
        else:
            self.boundary_smoothness = 0.5  # 默认中等
        metrics['boundary_smoothness'] = self.boundary_smoothness

        # 综合评分
        density_score = 1.0 if self.vertex_density >= min_density else self.vertex_density / min_density

        self.quality_score = (
            0.5 * self.confidence +
            0.3 * density_score +
            0.2 * self.boundary_smoothness
        )
        metrics['quality_score'] = round(self.quality_score, 3)

        return metrics

    def _calculate_perimeter(self) -> float:
        """计算多边形周长"""
        if not self.polygon or len(self.polygon) < 2:
            return 0.0

        perimeter = 0.0
        for i in range(len(self.polygon)):
            j = (i + 1) % len(self.polygon)
            dx = self.polygon[j][0] - self.polygon[i][0]
            dy = self.polygon[j][1] - self.polygon[i][1]
            perimeter += math.sqrt(dx * dx + dy * dy)
        return perimeter

    def _calculate_angle_changes(self) -> List[float]:
        """计算相邻边的角度变化"""
        if not self.polygon or len(self.polygon) < 3:
            return []

        angles = []
        n = len(self.polygon)
        for i in range(n):
            p1 = self.polygon[i]
            p2 = self.polygon[(i + 1) % n]
            p3 = self.polygon[(i + 2) % n]

            # 向量
            v1 = [p1[0] - p2[0], p1[1] - p2[1]]
            v2 = [p3[0] - p2[0], p3[1] - p2[1]]

            # 计算角度
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            mag1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
            mag2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])

            if mag1 > 0 and mag2 > 0:
                cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
                angle = math.degrees(math.acos(cos_angle))
                angles.append(angle)

        return angles

    def contains_point(self, x: int, y: int) -> bool:
        """检查点是否在标注区域内"""
        if self.mask is not None:
            if 0 <= y < self.mask.shape[0] and 0 <= x < self.mask.shape[1]:
                return self.mask[y, x] > 0.5
            return False

        if self.polygon:
            # Ray casting algorithm for polygon containment
            n = len(self.polygon)
            inside = False

            p1x, p1y = self.polygon[0]
            for i in range(1, n + 1):
                p2x, p2y = self.polygon[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y

            return inside

        # Check bbox
        bx, by, bw, bh = self.bbox
        return bx <= x <= bx + bw and by <= y <= by + bh


@dataclass
class ImageAnnotation:
    """单张图像的标注集合"""
    image_path: str = ""
    image_size: Tuple[int, int] = field(default_factory=lambda: (0, 0))
    annotations: List[Annotation] = field(default_factory=list)
    last_modified: str = ""

    def add_annotation(self, annotation: Annotation) -> int:
        """添加标注"""
        self.annotations.append(annotation)
        return annotation.id

    def remove_annotation(self, annotation_id: int) -> bool:
        """删除标注"""
        for i, ann in enumerate(self.annotations):
            if ann.id == annotation_id:
                self.annotations.pop(i)
                return True
        return False

    def get_annotation(self, annotation_id: int) -> Optional[Annotation]:
        """获取指定标注"""
        for ann in self.annotations:
            if ann.id == annotation_id:
                return ann
        return None

    def update_annotation(self, annotation_id: int, data: Dict[str, Any]) -> bool:
        """更新标注"""
        ann = self.get_annotation(annotation_id)
        if ann:
            ann.from_dict(data)
            return True
        return False

    def clear_annotations(self):
        """清除所有标注"""
        self.annotations.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "image_path": self.image_path,
            "image_size": list(self.image_size),
            "annotations": [ann.to_dict() for ann in self.annotations],
            "last_modified": self.last_modified
        }

    def from_dict(self, data: Dict[str, Any]) -> 'ImageAnnotation':
        """从字典创建"""
        self.image_path = data.get("image_path", "")
        self.image_size = tuple(data.get("image_size", (0, 0)))

        for ann_data in data.get("annotations", []):
            ann = Annotation()
            ann.from_dict(ann_data)
            self.annotations.append(ann)

        self.last_modified = data.get("last_modified", "")
        return self


@dataclass
class AnnotationProject:
    """标注项目"""
    name: str = "Untitled Project"
    project_path: str = ""
    images: List[ImageAnnotation] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "object", "id": 0, "color": "#00ff00"},
        {"name": "person", "id": 1, "color": "#ff0000"},
        {"name": "car", "id": 2, "color": "#0000ff"}
    ])

    def add_image(self, image_annotation: ImageAnnotation):
        """添加图像"""
        self.images.append(image_annotation)

    def remove_image(self, image_path: str):
        """删除图像"""
        self.images = [img for img in self.images if img.image_path != image_path]

    def get_image(self, image_path: str) -> Optional[ImageAnnotation]:
        """获取图像标注"""
        for img in self.images:
            if img.image_path == image_path:
                return img
        return None

    def get_class(self, class_id: int) -> Optional[Dict[str, Any]]:
        """获取类别信息"""
        for cls in self.classes:
            if cls["id"] == class_id:
                return cls
        return None

    def get_class_by_name(self, class_name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取类别"""
        for cls in self.classes:
            if cls["name"] == class_name:
                return cls
        return None

    def add_class(self, name: str, color: str) -> int:
        """添加新类别"""
        new_id = len(self.classes)
        self.classes.append({"name": name, "id": new_id, "color": color})
        return new_id

    def save(self, path: str):
        """保存项目"""
        data = {
            "name": self.name,
            "project_path": self.project_path,
            "classes": self.classes,
            "images": [img.to_dict() for img in self.images]
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> bool:
        """加载项目"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.name = data.get("name", "")
            self.project_path = data.get("project_path", "")
            self.classes = data.get("classes", self.classes)

            for img_data in data.get("images", []):
                img_ann = ImageAnnotation()
                img_ann.from_dict(img_data)
                self.images.append(img_ann)

            return True

        except Exception as e:
            print(f"Failed to load project: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_images = len(self.images)
        total_annotations = sum(len(img.annotations) for img in self.images)
        class_counts = {}

        for cls in self.classes:
            class_counts[cls["name"]] = 0

        for img in self.images:
            for ann in img.annotations:
                class_counts[ann.class_name] = class_counts.get(ann.class_name, 0) + 1

        return {
            "total_images": total_images,
            "total_annotations": total_annotations,
            "class_counts": class_counts
        }