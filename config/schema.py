"""配置Schema定义 - 类型安全配置管理"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class OutputFormat(Enum):
    JPG = "jpg"
    PNG = "png"


class NamingMode(Enum):
    SEQUENCE = "sequence"
    TIMESTAMP = "timestamp"
    CUSTOM = "custom"


class PairingMode(Enum):
    BY_NAME = "name"
    BY_SEQUENCE = "sequence"


@dataclass
class FrameExtractorConfig:
    """视频切帧配置"""
    start_time: float = 0.0
    end_time: float = 10.0
    sample_fps: float = 1.0
    output_format: str = "jpg"
    quality: int = 95
    naming_mode: str = "sequence"
    custom_prefix: str = "frame"
    start_number: int = 1
    digit_length: int = 6
    time_format: str = "%Y%m%d_%H%M%S"
    use_same_output_dir: bool = True
    create_subfolder: bool = True
    subfolder_name: str = "frames_{video_name}"
    
    def validate(self) -> List[str]:
        errors = []
        if self.start_time < 0:
            errors.append("起始时间不能为负数")
        if self.end_time <= self.start_time:
            errors.append("结束时间必须大于起始时间")
        if self.sample_fps <= 0:
            errors.append("采样帧率必须大于0")
        if not 50 <= self.quality <= 100:
            errors.append("JPEG质量必须在50-100之间")
        return errors


@dataclass
class RenamerConfig:
    """文件重命名配置"""
    file_type: str = "txt"
    start_number: int = 1
    digit_width: int = 6


@dataclass
class ClassMappingConfig:
    """YOLO类别映射配置"""
    mapping: Dict[int, str] = field(default_factory=lambda: {
        0: "开水器",
        1: "纸杯",
        2: "厕所",
        3: "灭火器",
        4: "马桶",
        5: "水槽"
    })
    
    def add_class(self, class_id: int, name: str) -> None:
        self.mapping[class_id] = name
        
    def remove_class(self, class_id: int) -> bool:
        return self.mapping.pop(class_id, None) is not None
    
    def get_next_id(self) -> int:
        return max(self.mapping.keys()) + 1 if self.mapping else 0
    
    def to_dict(self) -> Dict:
        return self.mapping
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClassMappingConfig':
        return cls(mapping={int(k): v for k, v in data.items()})


@dataclass
class AppSettings:
    """应用程序全局设置"""
    last_output_dir: str = ""
    last_folder_path: str = ""
    window_width: int = 900
    window_height: int = 700
    theme: str = "default"
    
    def validate(self) -> List[str]:
        errors = []
        if self.window_width < 600 or self.window_height < 400:
            errors.append("窗口尺寸过小")
        return errors
