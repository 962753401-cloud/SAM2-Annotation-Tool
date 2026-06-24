"""Quality Metrics 单元测试"""

import pytest
import math
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.annotation_data import Annotation


class TestQualityMetrics:
    """质量指标测试类"""

    def test_quality_metrics_basic(self):
        """测试基本质量指标计算"""
        ann = Annotation(
            class_name="test",
            label="测试标注",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]],
            bbox=[10, 10, 40, 40],
            confidence=0.95
        )

        metrics = ann.calculate_quality_metrics()

        # 验证各项指标存在
        assert 'vertex_count' in metrics
        assert 'perimeter' in metrics
        assert 'vertex_density' in metrics
        assert 'boundary_smoothness' in metrics
        assert 'quality_score' in metrics

        # 验证顶点数
        assert ann.vertex_count == 4
        assert metrics['vertex_count'] == 4

        # 验证综合评分范围
        assert 0 <= ann.quality_score <= 1

    def test_quality_metrics_empty_polygon(self):
        """测试空polygon的质量指标"""
        ann = Annotation(
            class_name="test",
            label="空polygon",
            confidence=0.8
        )

        metrics = ann.calculate_quality_metrics()

        # 空polygon应该有默认值
        assert ann.vertex_count == 0
        assert ann.vertex_density == 0
        assert metrics['vertex_count'] == 0

        # 不应该崩溃
        assert True

    def test_quality_metrics_single_point(self):
        """测试单点polygon"""
        ann = Annotation(
            class_name="test",
            polygon=[[10, 10]],
            confidence=0.9
        )

        metrics = ann.calculate_quality_metrics()

        # 单点polygon周长为0
        assert ann.vertex_count == 1
        assert metrics['perimeter'] == 0
        # 密度为0（因为周长为0）
        assert ann.vertex_density == 0

    def test_quality_metrics_two_points(self):
        """测试两点polygon"""
        ann = Annotation(
            class_name="test",
            polygon=[[10, 10], [100, 10]],
            confidence=0.9
        )

        metrics = ann.calculate_quality_metrics()

        # 两点polygon有周长
        assert ann.vertex_count == 2
        assert metrics['perimeter'] == 180  # 90 + 90 (往返)
        # 密度计算
        assert ann.vertex_density >= 0

    def test_quality_metrics_complex_polygon(self):
        """测试复杂多边形（多顶点）"""
        # 创建一个圆形近似的多边形（多顶点）
        points = []
        for i in range(20):
            angle = 2 * math.pi * i / 20
            x = int(100 + 50 * math.cos(angle))
            y = int(100 + 50 * math.sin(angle))
            points.append([x, y])

        ann = Annotation(
            class_name="test",
            polygon=points,
            confidence=0.85
        )

        metrics = ann.calculate_quality_metrics()

        # 验证顶点数
        assert ann.vertex_count == 20

        # 圆形应该有较高的平滑度
        assert ann.boundary_smoothness > 0.5

        # 综合评分应该合理
        assert 0 <= ann.quality_score <= 1

    def test_quality_metrics_rectangle_high_score(self):
        """测试矩形应该有较高平滑度评分"""
        ann = Annotation(
            class_name="test",
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]],
            confidence=0.9
        )

        metrics = ann.calculate_quality_metrics()

        # 矩形（简单形状）默认高平滑度评分
        assert ann.boundary_smoothness >= 0.8

    def test_quality_metrics_with_config(self):
        """测试带配置的质量指标计算"""
        ann = Annotation(
            class_name="test",
            polygon=[[10, 10], [50, 10], [50, 50], [10, 50]],
            confidence=0.9
        )

        config = {
            'min_vertex_density': 10  # 设置更高的最小密度要求
        }

        metrics = ann.calculate_quality_metrics(config)

        # 验证配置被应用
        assert 'quality_score' in metrics

    def test_perimeter_calculation(self):
        """测试周长计算"""
        # 正方形
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )

        perimeter = ann._calculate_perimeter()
        assert perimeter == 400  # 100*4

    def test_perimeter_empty_polygon(self):
        """测试空polygon周长"""
        ann = Annotation()
        perimeter = ann._calculate_perimeter()
        assert perimeter == 0

    def test_angle_changes_calculation(self):
        """测试角度变化计算"""
        # 正方形 - 每个角90度
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )

        angles = ann._calculate_angle_changes()
        assert len(angles) == 4
        # 正方形每个角度变化应该接近90度
        for angle in angles:
            assert 80 <= angle <= 100  # 允许误差

    def test_vertex_density_formula(self):
        """测试顶点密度公式"""
        # 周长400px，顶点4个
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        )

        ann.calculate_quality_metrics()

        # 密度 = 4 / (400/100) = 4 / 4 = 1
        expected_density = 4 / 4
        assert abs(ann.vertex_density - expected_density) < 0.1

    def test_vertex_density_upper_limit(self):
        """测试顶点密度上限"""
        # 创建很多顶点的小多边形
        points = [[i, i] for i in range(50)]
        ann = Annotation(
            polygon=points
        )

        ann.calculate_quality_metrics()

        # 密度上限为20
        assert ann.vertex_density <= 20

    def test_quality_score_formula(self):
        """测试综合评分公式"""
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]],
            confidence=0.9
        )

        ann.calculate_quality_metrics()

        # 验证评分组成
        # 0.5 * confidence + 0.3 * density_score + 0.2 * smoothness
        # 应该在合理范围内
        assert ann.quality_score >= 0.5 * 0.9  # 至少有置信度贡献

    def test_to_dict_includes_quality_fields(self):
        """测试to_dict包含质量字段"""
        ann = Annotation(
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]],
            confidence=0.9
        )

        ann.calculate_quality_metrics()
        data = ann.to_dict()

        # 验证新字段存在
        assert 'quality_score' in data
        assert 'boundary_smoothness' in data
        assert 'vertex_count' in data
        assert 'vertex_density' in data

    def test_from_dict_loads_quality_fields(self):
        """测试from_dict加载质量字段"""
        data = {
            'id': 123,
            'class_name': 'test',
            'polygon': [[0, 0], [100, 0], [100, 100], [0, 100]],
            'quality_score': 0.85,
            'boundary_smoothness': 0.9,
            'vertex_count': 4,
            'vertex_density': 1.0
        }

        ann = Annotation()
        ann.from_dict(data)

        # 验证字段被加载
        assert ann.quality_score == 0.85
        assert ann.boundary_smoothness == 0.9
        assert ann.vertex_count == 4
        assert ann.vertex_density == 1.0

    def test_from_dict_backward_compatibility(self):
        """测试from_dict向后兼容（旧数据无质量字段）"""
        # 旧数据格式（无质量字段）
        data = {
            'id': 123,
            'class_name': 'test',
            'polygon': [[0, 0], [100, 0], [100, 100], [0, 100]],
            'confidence': 0.9
        }

        ann = Annotation()
        ann.from_dict(data)

        # 应该使用默认值，不崩溃
        assert ann.quality_score == 0.0
        assert ann.boundary_smoothness == 0.0
        assert ann.vertex_count == 4  # 从polygon计算
        assert ann.vertex_density == 0.0


class TestConfigLoaderQuality:
    """ConfigLoader质量配置测试"""

    def test_get_polygon_config(self):
        """测试获取polygon配置"""
        from src.utils.config_loader import ConfigLoader

        config = ConfigLoader()
        polygon_config = config.get_polygon_config()

        assert 'epsilon_factor' in polygon_config
        assert 'max_vertices' in polygon_config
        assert polygon_config['epsilon_factor'] > 0
        assert polygon_config['max_vertices'] > 0

    def test_get_quality_config(self):
        """测试获取quality配置"""
        from src.utils.config_loader import ConfigLoader

        config = ConfigLoader()
        quality_config = config.get_quality_config()

        assert 'enable_metrics' in quality_config
        assert 'min_vertex_density' in quality_config

    def test_get_classes_with_hierarchy(self):
        """测试获取带层级类别"""
        from src.utils.config_loader import ConfigLoader

        config = ConfigLoader()
        classes = config.get_classes_with_hierarchy()

        assert len(classes) > 0
        # 验证每个类别有必要字段
        for cls in classes:
            assert 'name' in cls
            assert 'id' in cls
            assert 'supercategory' in cls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])