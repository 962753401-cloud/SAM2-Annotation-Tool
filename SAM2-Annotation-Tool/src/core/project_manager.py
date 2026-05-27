"""Project Manager for annotation projects"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from .annotation_data import AnnotationProject, ImageAnnotation, Annotation


class ProjectManager:
    """项目管理器"""

    def __init__(self):
        self.project: Optional[AnnotationProject] = None
        self.project_path: str = ""
        self.is_saved: bool = True

    def create_project(self, name: str, save_path: str) -> AnnotationProject:
        """创建新项目"""
        self.project = AnnotationProject(name=name, project_path=save_path)
        self.project_path = save_path
        self.is_saved = False
        return self.project

    def load_project(self, path: str) -> Optional[AnnotationProject]:
        """加载项目"""
        self.project = AnnotationProject()
        if self.project.load(path):
            self.project_path = path
            self.is_saved = True
            return self.project
        return None

    def save_project(self, path: Optional[str] = None) -> bool:
        """保存项目"""
        if self.project is None:
            return False

        save_path = path or self.project_path
        if not save_path:
            return False

        self.project.save(save_path)
        self.project_path = save_path
        self.is_saved = True
        return True

    def get_current_project(self) -> Optional[AnnotationProject]:
        """获取当前项目"""
        return self.project

    def add_image_to_project(self, image_path: str, image_size: tuple) -> ImageAnnotation:
        """向项目添加图像"""
        if self.project is None:
            return None

        img_ann = ImageAnnotation(
            image_path=image_path,
            image_size=image_size,
            last_modified=datetime.now().isoformat()
        )
        self.project.add_image(img_ann)
        self.is_saved = False
        return img_ann

    def get_image_annotation(self, image_path: str) -> Optional[ImageAnnotation]:
        """获取图像的标注"""
        if self.project is None:
            return None
        return self.project.get_image(image_path)

    def add_annotation(self, image_path: str, annotation: Annotation) -> bool:
        """添加标注"""
        if self.project is None:
            return False

        img_ann = self.project.get_image(image_path)
        if img_ann is None:
            return False

        img_ann.add_annotation(annotation)
        img_ann.last_modified = datetime.now().isoformat()
        self.is_saved = False
        return True

    def remove_annotation(self, image_path: str, annotation_id: int) -> bool:
        """删除标注"""
        if self.project is None:
            return False

        img_ann = self.project.get_image(image_path)
        if img_ann is None:
            return False

        result = img_ann.remove_annotation(annotation_id)
        if result:
            img_ann.last_modified = datetime.now().isoformat()
            self.is_saved = False
        return result

    def update_annotation(self, image_path: str, annotation_id: int, data: Dict[str, Any]) -> bool:
        """更新标注"""
        if self.project is None:
            return False

        img_ann = self.project.get_image(image_path)
        if img_ann is None:
            return False

        result = img_ann.update_annotation(annotation_id, data)
        if result:
            img_ann.last_modified = datetime.now().isoformat()
            self.is_saved = False
        return result

    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改"""
        return not self.is_saved

    def export_annotations(self, output_dir: str, format: str = "coco") -> bool:
        """导出标注"""
        if self.project is None:
            return False

        # This will be implemented by exporters
        return True