"""Configuration Schema Definition - Type-safe configuration management"""
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
    """Video frame extraction configuration"""
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
            errors.append("Start time cannot be negative")
        if self.end_time <= self.start_time:
            errors.append("End time must be greater than start time")
        if self.sample_fps <= 0:
            errors.append("Sample FPS must be greater than 0")
        if not 50 <= self.quality <= 100:
            errors.append("JPEG quality must be between 50-100")
        return errors


@dataclass
class RenamerConfig:
    """File renaming configuration"""
    file_type: str = "txt"
    start_number: int = 1
    digit_width: int = 6


@dataclass
class ClassMappingConfig:
    """YOLO class mapping configuration"""
    mapping: Dict[int, str] = field(default_factory=lambda: {
        0: "water_heater",
        1: "paper_cup",
        2: "toilet",
        3: "fire_extinguisher",
        4: "commode",
        5: "sink"
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
    """Application global settings"""
    last_output_dir: str = ""
    last_folder_path: str = ""
    window_width: int = 900
    window_height: int = 700
    theme: str = "default"
    
    def validate(self) -> List[str]:
        errors = []
        if self.window_width < 600 or self.window_height < 400:
            errors.append("Window size is too small")
        return errors