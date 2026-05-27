"""VOC XML Exporter"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from .base_exporter import BaseExporter
from ..core.annotation_data import AnnotationProject, ImageAnnotation, Annotation


class VOCExporter(BaseExporter):
    """VOC XML格式导出器"""

    def __init__(self, output_dir: str, project_name: str = "project"):
        super().__init__(output_dir)
        self.project_name = self._sanitize_filename(project_name)
        self.annotations_dir = os.path.join(output_dir, "Annotations")
        self.images_dir = os.path.join(output_dir, "JPEGImages")
        os.makedirs(self.annotations_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        name = name.strip()
        if not name:
            name = "unnamed"
        return name

    def export(self, project: AnnotationProject) -> bool:
        """导出项目为VOC格式"""
        if project is None:
            return False

        try:
            # Export each image annotation
            for img_ann in project.images:
                self.export_image_annotation(img_ann, project.classes)

            # Create dataset info files
            self.create_dataset_info(project)

            return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def export_image_annotation(self, img_ann: ImageAnnotation, classes: List[Dict]) -> str:
        """导出单张图像的标注"""
        annotation = ET.Element("annotation")

        # Folder
        folder = ET.SubElement(annotation, "folder")
        folder.text = "JPEGImages"

        # Filename
        filename = ET.SubElement(annotation, "filename")
        filename.text = os.path.basename(img_ann.image_path)

        # Path
        path = ET.SubElement(annotation, "path")
        path.text = img_ann.image_path

        # Source
        source = ET.SubElement(annotation, "source")
        database = ET.SubElement(source, "database")
        database.text = "SAM2 Annotation Tool"

        # Size
        size = ET.SubElement(annotation, "size")
        width = ET.SubElement(size, "width")
        width.text = str(img_ann.image_size[0])
        height = ET.SubElement(size, "height")
        height.text = str(img_ann.image_size[1])
        depth = ET.SubElement(size, "depth")
        depth.text = "3"

        # Segmented
        segmented = ET.SubElement(annotation, "segmented")
        segmented.text = "1"  # Indicates segmentation data exists

        # Objects
        for ann in img_ann.annotations:
            obj = self.create_object_element(ann, classes)
            annotation.append(obj)

        # 生成新的文件名：{项目名}_{原图片名}_{时间戳}.xml
        original_name = os.path.splitext(os.path.basename(img_ann.image_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_filename = f"{self.project_name}_{original_name}_{timestamp}.xml"
        xml_path = os.path.join(self.annotations_dir, xml_filename)

        self.write_xml(annotation, xml_path)

        return xml_path

    def create_object_element(self, ann: Annotation, classes: List[Dict]) -> ET.Element:
        """创建object元素"""
        obj = ET.Element("object")

        # Name
        name = ET.SubElement(obj, "name")
        name.text = ann.class_name

        # Label (text annotation)
        if ann.label:
            label_elem = ET.SubElement(obj, "label")
            label_elem.text = ann.label

        # Quality metrics (新增)
        quality = ET.SubElement(obj, "quality")
        quality_score = ET.SubElement(quality, "score")
        quality_score.text = str(round(ann.quality_score, 3))
        boundary_smoothness = ET.SubElement(quality, "smoothness")
        boundary_smoothness.text = str(round(ann.boundary_smoothness, 3))
        vertex_count = ET.SubElement(quality, "vertices")
        vertex_count.text = str(ann.vertex_count)
        vertex_density = ET.SubElement(quality, "density")
        vertex_density.text = str(round(ann.vertex_density, 2))

        # Pose
        pose = ET.SubElement(obj, "pose")
        pose.text = "Unspecified"

        # Truncated
        truncated = ET.SubElement(obj, "truncated")
        truncated.text = "0"

        # Difficult
        difficult = ET.SubElement(obj, "difficult")
        difficult.text = "0"

        # Bounding box
        bndbox = ET.SubElement(obj, "bndbox")
        xmin = ET.SubElement(bndbox, "xmin")
        xmin.text = str(ann.bbox[0])
        ymin = ET.SubElement(bndbox, "ymin")
        ymin.text = str(ann.bbox[1])
        xmax = ET.SubElement(bndbox, "xmax")
        xmax.text = str(ann.bbox[0] + ann.bbox[2])
        ymax = ET.SubElement(bndbox, "ymax")
        ymax.text = str(ann.bbox[1] + ann.bbox[3])

        # Polygon (for segmentation)
        if ann.polygon and len(ann.polygon) >= 3:
            polygon = ET.SubElement(obj, "polygon")
            for i, point in enumerate(ann.polygon):
                pt = ET.SubElement(polygon, f"pt{i}")
                x = ET.SubElement(pt, "x")
                x.text = str(point[0])
                y = ET.SubElement(pt, "y")
                y.text = str(point[1])

        return obj

    def write_xml(self, root: ET.Element, path: str):
        """写入格式化的XML"""
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def create_dataset_info(self, project: AnnotationProject):
        """创建数据集信息文件"""
        # Create train.txt
        train_list_path = os.path.join(self.output_dir, "train.txt")
        with open(train_list_path, 'w') as f:
            for img_ann in project.images:
                basename = os.path.splitext(os.path.basename(img_ann.image_path))[0]
                f.write(basename + '\n')

        # Create classes list
        classes_path = os.path.join(self.output_dir, "classes.txt")
        with open(classes_path, 'w') as f:
            for cls in project.classes:
                f.write(cls["name"] + '\n')