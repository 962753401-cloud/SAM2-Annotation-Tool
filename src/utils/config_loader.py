"""Configuration Loader"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config: Dict[str, Any] = {}

        # Default config path
        if config_path is None:
            # Look for config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"

        self.config_path = str(config_path)

        # Load config
        self.load()

    def load(self) -> bool:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                return True

            # Use default config if file not found
            self.config = self.get_default_config()
            return False

        except Exception as e:
            print(f"Failed to load config: {e}")
            self.config = self.get_default_config()
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "model": {
                "path": "D:/模型库/SAM2/sam2_hiera_tiny.pt",
                "device": "cuda",
                "dtype": "bfloat16"
            },
            "polygon": {
                "epsilon_factor": 0.005,
                "max_vertices": 100
            },
            "quality": {
                "enable_metrics": True,
                "min_vertex_density": 5
            },
            "features": {
                "high_density_polygon": True,
                "quality_metrics": True,
                "class_hierarchy": False
            },
            "ui": {
                "theme": "dark",
                "mask_opacity": 0.5,
                "polygon_line_width": 2,
                "point_size": 8
            },
            "classes": [
                {"name": "object", "id": 0, "color": "#00ff00", "supercategory": "general"},
                {"name": "person", "id": 1, "color": "#ff0000", "supercategory": "living"},
                {"name": "car", "id": 2, "color": "#0000ff", "supercategory": "vehicle"}
            ],
            "export": {
                "default_format": "coco",
                "output_dir": "./annotations"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持嵌套键）"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()

    def get_polygon_config(self) -> Dict[str, Any]:
        """获取多边形配置"""
        return {
            'epsilon_factor': self.get('polygon.epsilon_factor', 0.005),
            'max_vertices': self.get('polygon.max_vertices', 100)
        }

    def get_quality_config(self) -> Dict[str, Any]:
        """获取质量评估配置"""
        return {
            'enable_metrics': self.get('quality.enable_metrics', True),
            'min_vertex_density': self.get('quality.min_vertex_density', 5)
        }

    def get_features_config(self) -> Dict[str, Any]:
        """获取功能开关配置"""
        return {
            'high_density_polygon': self.get('features.high_density_polygon', True),
            'quality_metrics': self.get('features.quality_metrics', True),
            'class_hierarchy': self.get('features.class_hierarchy', False)
        }

    def get_classes_with_hierarchy(self) -> list:
        """获取带层级结构的类别列表"""
        classes = self.get('classes', [])
        # 确保每个类别都有id和supercategory字段
        for i, cls in enumerate(classes):
            if 'id' not in cls:
                cls['id'] = i
            if 'supercategory' not in cls:
                cls['supercategory'] = 'general'
        return classes

    def get_classes_flat(self) -> list:
        """获取扁平化的类别列表（不含层级信息，用于兼容旧代码）"""
        classes = self.get('classes', [])
        return [{"name": cls.get('name', 'object'), "color": cls.get('color', '#00ff00')}
                for cls in classes]