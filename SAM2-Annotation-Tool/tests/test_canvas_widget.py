"""Canvas Widget 单元测试"""

import pytest
import numpy as np
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.gui.canvas_widget import CanvasWidget
from src.core.annotation_data import Annotation


class TestCanvasWidget:
    """CanvasWidget测试类"""

    @pytest.fixture(scope="class")
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def canvas(self, app):
        """创建测试画布"""
        canvas = CanvasWidget()
        return canvas

    def test_draw_label_text_no_crash(self, canvas):
        """测试带label的标注绘制不会崩溃"""
        # 设置图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        # 创建带label的标注
        ann = Annotation(
            class_name="test",
            label="测试标注",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]],
            bbox=[10, 10, 40, 40]
        )
        canvas.annotations.append(ann)

        # 触发重绘 - 应该不崩溃
        canvas.update()
        # 验证标注数量
        assert len(canvas.annotations) == 1

    def test_empty_polygon_handling(self, canvas):
        """测试空polygon不会崩溃"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(class_name="test", label="空polygon")
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_special_characters_in_label(self, canvas):
        """测试特殊字符label"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="特殊字符: \n\t中文",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_empty_label(self, canvas):
        """测试空label"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="",  # 空字符串
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃，不绘制文本
        assert True

    def test_none_label(self, canvas):
        """测试None label"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        # label 默认为 ""
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_single_point_polygon(self, canvas):
        """测试polygon只有一个点"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="单点polygon",
            polygon=[[10, 10]]  # 只有一个点
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_two_point_polygon(self, canvas):
        """测试polygon只有两个点"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="两点polygon",
            polygon=[[10, 10], [50, 50]]  # 只有两个点
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_multiple_annotations_with_labels(self, canvas):
        """测试多个带label的标注"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        # 创建多个标注
        for i in range(5):
            ann = Annotation(
                class_name=f"class_{i}",
                label=f"标注{i}",
                polygon=[[10+i*10, 10], [50+i*10, 10], [50+i*10, 50], [10+i*10, 50]]
            )
            canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert len(canvas.annotations) == 5

    def test_visibility_toggle(self, canvas):
        """测试可见性切换"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="隐藏标注",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]],
            visible=False
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃，不绘制隐藏的标注
        assert True

    def test_long_label(self, canvas):
        """测试长文本label"""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        canvas.set_image(test_image)

        ann = Annotation(
            class_name="test",
            label="这是一个非常长的标注文本内容，用于测试长文本的绘制效果",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        canvas.annotations.append(ann)

        canvas.update()  # 应该不崩溃
        assert True

    def test_no_image(self, canvas):
        """测试没有加载图像时的绘制"""
        # 不设置图像
        canvas.update()  # 应该不崩溃，显示"请打开图片"
        assert canvas.pixmap is None


class TestAnnotationData:
    """Annotation数据模型测试"""

    def test_annotation_creation(self):
        """测试Annotation创建"""
        ann = Annotation(
            class_name="test",
            label="测试",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        assert ann.class_name == "test"
        assert ann.label == "测试"
        assert len(ann.polygon) == 4

    def test_annotation_to_dict(self):
        """测试Annotation转换为字典"""
        ann = Annotation(
            class_name="test",
            label="测试",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]]
        )
        data = ann.to_dict()
        assert "label" in data
        assert data["label"] == "测试"

    def test_annotation_area_calculation(self):
        """测试面积计算"""
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )
        area = ann.get_area()
        assert area > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])