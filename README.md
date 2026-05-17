# YORO-You Only Run Once

## 项目简介

这是一个基于YOLO训练数据与应用分析的一站式项目，已完成模块化重构，采用分层架构设计。

### 功能模块

1. **视频切帧工具** - 从视频中按时间或帧率提取图片帧
2. **批量文件重命名** - 支持TXT和图片文件的批量序号重命名
3. **孤立文件清理** - 清理图片与标注文件不匹配的情况
4. **YOLO标注统计** - 统计YOLO标注文件中各类别的数量

## 项目结构

```
YOLO-Train/
├── config/                      # 配置层
│   ├── __init__.py
│   └── schema.py               # 配置数据结构定义
├── core/                        # 核心业务逻辑层
│   ├── __init__.py
│   ├── base.py                  # 抽象基类
│   ├── file_operator.py         # 文件操作公共逻辑
│   ├── natural_sort.py          # 自然排序算法
│   └── validators.py            # 数据验证器
├── modules/                     # 功能模块层
│   ├── __init__.py
│   ├── frame_extractor/         # 视频切帧模块
│   │   ├── extractor.py         # 切帧核心逻辑
│   │   └── gui.py              # GUI组件
│   ├── file_renamer/           # 文件重命名模块
│   │   ├── renamer.py          # 重命名核心逻辑
│   │   └── gui.py
│   ├── orphan_cleaner/         # 孤立文件清理模块
│   │   ├── cleaner.py          # 清理核心逻辑
│   │   └── gui.py
│   └── yolo_stats/             # YOLO统计模块
│       ├── counter.py          # 统计核心逻辑
│       └── gui.py
├── ui/                          # 公共UI组件层
│   ├── __init__.py
│   ├── components.py            # 公共UI组件
│   └── theme.py                 # 主题样式
├── utils/                       # 工具层
│   ├── __init__.py
│   ├── logger.py               # 日志工具
│   ├── persistence.py           # 持久化工具
│   └── thread_pool.py          # 线程池工具
├── tests/                        # 测试模块
│   ├── __init__.py
│   └── test_modules.py         # 模块测试脚本
├── main.py                      # 程序入口
└── app.py                       # 主应用程序
```

## 快速开始

### 环境要求

- Python 3.8+
- tkinter (通常随Python一起安装)
- opencv-python (用于视频切帧功能，可选)

### 安装依赖

```bash
pip install opencv-python numpy
```

### 运行程序

```bash
python main.py
```

### 运行测试

```bash
python tests/test_modules.py
```

## 架构设计

### 分层架构

- **config层**: 配置文件和Schema定义
- **core层**: 核心业务逻辑，与UI解耦
- **modules层**: 功能模块，整合core和gui
- **ui层**: 公共UI组件
- **utils层**: 通用工具类

### 核心特性

1. **模块化设计**: 各功能模块独立，易于维护和扩展
2. **配置持久化**: 支持配置的自动保存和加载
3. **线程池支持**: 后台任务执行，不阻塞UI
4. **类型安全**: 使用dataclass和枚举定义配置
5. **依赖注入**: 单例模式的全局管理器

## API使用示例

### 配置管理

```python
from config.schema import FrameExtractorConfig, ClassMappingConfig

# 视频切帧配置
config = FrameExtractorConfig(
    start_time=0.0,
    end_time=10.0,
    sample_fps=1.0,
    output_format="jpg"
)

# YOLO类别映射配置
class_config = ClassMappingConfig()
class_config.add_class(10, "新类别")
```

### 日志工具

```python
from utils import Logger

logger = Logger.get_instance()
logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
logger.success("成功日志")
```

### 文件验证

```python
from core import Validator

is_valid, msg = Validator.validate_directory("/path/to/dir")
is_valid, msg = Validator.validate_video_file("/path/to/video.mp4")
```

## 扩展开发

### 添加新模块

1. 在 `modules/` 下创建新模块目录
2. 创建 `core.py` 实现核心逻辑（继承 `core.base.BaseModule`）
3. 创建 `gui.py` 实现GUI组件
4. 在 `modules/__init__.py` 中导出模块
5. 在 `app.py` 的notebook中添加新标签页

### 示例：添加新模块

```python
# modules/my_module/core.py
from core.base import BaseModule

class MyModuleCore(BaseModule):
    def __init__(self):
        super().__init__()
    
    def get_name(self) -> str:
        return "我的模块"
    
    def process(self, data):
        # 核心业务逻辑
        pass

# modules/my_module/gui.py
import tkinter as tk
from tkinter import ttk

class MyModuleGUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # GUI组件
        pass
```

## 版本历史

### v2.0 (当前版本)

- 完成模块化重构
- 采用分层架构设计
- 新增配置持久化
- 新增单元测试

### v1.0 (原始版本)

- 基础功能实现
- 独立脚本文件

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。
