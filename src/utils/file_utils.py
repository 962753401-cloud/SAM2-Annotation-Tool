"""File Utilities"""

import os
import shutil
from typing import List, Optional
from pathlib import Path


class FileUtils:
    """文件操作工具"""

    @staticmethod
    def ensure_dir(path: str) -> bool:
        """确保目录存在"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create directory: {e}")
            return False

    @staticmethod
    def get_file_list(directory: str, extensions: List[str] = None) -> List[str]:
        """获取目录中的文件列表"""
        if not os.path.exists(directory):
            return []

        files = []

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)

            if os.path.isfile(filepath):
                if extensions:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extensions:
                        files.append(filepath)
                else:
                    files.append(filepath)

        return sorted(files)

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """复制文件"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Failed to copy file: {e}")
            return False

    @staticmethod
    def delete_file(path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False

    @staticmethod
    def get_basename(path: str) -> str:
        """获取文件基本名称（无扩展名）"""
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def get_extension(path: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(path)[1].lower()

    @staticmethod
    def join_path(*args) -> str:
        """拼接路径"""
        return os.path.join(*args)

    @staticmethod
    def exists(path: str) -> bool:
        """检查路径是否存在"""
        return os.path.exists(path)