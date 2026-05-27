"""COCO JSON Exporter"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime
from .base_exporter import BaseExporter
from ..core.annotation_data import AnnotationProject, ImageAnnotation, Annotation


class COCOExporter(BaseExporter):
    """COCO JSON格式导出器"""

    def __init__(self, output_dir: str, project_name: str = "project", image_name: str = "image"):
        super().__init__(output_dir)
        # 清理文件名中的非法字符
        safe_project = self._sanitize_filename(project_name)
        safe_image = self._sanitize_filename(image_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_project}_{safe_image}_{timestamp}.json"
        self.output_file = os.path.join(output_dir, filename)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除路径分隔符和常见非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # 移除前后空格
        name = name.strip()
        # 如果为空，使用默认值
        if not name:
            name = "unnamed"
        return name

    def export(self, project: AnnotationProject) -> bool:
        """导出项目为COCO格式"""
        if project is None:
            return False

        try:
            coco_data = self.create_coco_structure(project)

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(coco_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def create_coco_structure(self, project: AnnotationProject) -> Dict[str, Any]:
        """创建COCO数据结构"""
        coco = {
            "info": self.create_info(project),
            "licenses": [],
            "categories": self.create_categories(project.classes),
            "images": [],
            "annotations": []
        }

        annotation_id = 1

        for img_ann in project.images:
            # Add image info
            image_id = len(coco["images"]) + 1
            coco["images"].append(self.create_image_info(img_ann, image_id))

            # Add annotations for this image
            for ann in img_ann.annotations:
                coco_ann = self.create_annotation_info(ann, image_id, annotation_id)
                coco["annotations"].append(coco_ann)
                annotation_id += 1

        return coco

    def create_info(self, project: AnnotationProject) -> Dict[str, Any]:
        """创建info字段"""
        return {
            "description": f"SAM2 Annotation Tool Export - {project.name}",
            "url": "",
            "version": "1.0.0",
            "year": datetime.now().year,
            "contributor": "",
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def create_categories(self, classes: List[Dict]) -> List[Dict]:
        """创建categories字段"""
        categories = []

        for i, cls in enumerate(classes):
            categories.append({
                "id": cls.get("id", i),
                "name": cls["name"],
                "supercategory": cls.get("supercategory", "")
            })

        return categories

    def create_image_info(self, img_ann: ImageAnnotation, image_id: int) -> Dict[str, Any]:
        """创建image字段"""
        return {
            "id": image_id,
            "file_name": os.path.basename(img_ann.image_path),
            "width": img_ann.image_size[0],
            "height": img_ann.image_size[1],
            "coco_url": "",
            "flickr_url": "",
            "date_captured": img_ann.last_modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def create_annotation_info(self, ann: Annotation, image_id: int, annotation_id: int) -> Dict[str, Any]:
        """创建annotation字段"""
        # Bounding box in COCO format: [x, y, width, height]
        bbox = ann.bbox if ann.bbox and len(ann.bbox) >= 4 else [0, 0, 0, 0]

        # Area
        area = ann.get_area()

        # Segmentation - COCO supports polygon format
        segmentation = []

        print(f"Exporting annotation {annotation_id}: polygon={ann.polygon}, bbox={ann.bbox}, len={len(ann.polygon) if ann.polygon else 0}")

        if ann.polygon and len(ann.polygon) >= 3:
            # Flatten polygon points for COCO
            polygon_flat = []
            for point in ann.polygon:
                polygon_flat.extend([float(point[0]), float(point[1])])
            segmentation.append(polygon_flat)
            print(f"Polygon flattened: {len(polygon_flat)} points")

        # RLE encoding for masks (optional)
        # If mask is available, could convert to RLE
        # segmentation_rle = self.mask_to_rle(ann.mask)

        return {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": ann.class_id,
            "segmentation": segmentation,
            "area": area,
            "bbox": bbox,
            "iscrowd": 0,
            "attributes": {
                "confidence": ann.confidence,
                "is_manual": ann.is_manual,
                "label": ann.label,
                # 新增质量指标字段
                "quality_score": ann.quality_score,
                "boundary_smoothness": ann.boundary_smoothness,
                "vertex_count": ann.vertex_count,
                "vertex_density": ann.vertex_density
            }
        }

    def mask_to_rle(self, mask) -> Dict[str, Any]:
        """将掩码转为RLE格式（可选）"""
        if mask is None:
            return {"counts": [], "size": [0, 0]}

        # Simple RLE encoding
        # COCO uses RLE for mask representation
        # This is a basic implementation
        import numpy as np

        binary_mask = (mask > 0.5).astype(np.uint8)
        h, w = binary_mask.shape

        # Flatten and encode
        flat = binary_mask.flatten(order='F')
        runs = []

        pos = 0
        while pos < len(flat):
            # Find run of zeros
            start = pos
            while pos < len(flat) and flat[pos] == 0:
                pos += 1
            runs.append(pos - start)

            # Find run of ones
            start = pos
            while pos < len(flat) and flat[pos] == 1:
                pos += 1
            runs.append(pos - start)

        return {
            "counts": runs,
            "size": [h, w]
        }