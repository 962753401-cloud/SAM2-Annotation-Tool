"""Base Exporter"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path
import os


class BaseExporter(ABC):
    """导出器基类"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    @abstractmethod
    def export(self, project) -> bool:
        """导出标注数据"""
        pass

    def get_output_path(self, filename: str) -> str:
        """获取输出路径"""
        return os.path.join(self.output_dir, filename)