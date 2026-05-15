"""数据验证器 - 提供输入验证功能"""
import os
from typing import List, Tuple, Any
from pathlib import Path


class Validator:
    """通用验证器"""
    
    @staticmethod
    def validate_directory(path: str) -> Tuple[bool, str]:
        """验证目录是否存在且可访问"""
        if not path:
            return False, "目录路径不能为空"
        if not os.path.exists(path):
            return False, f"目录不存在: {path}"
        if not os.path.isdir(path):
            return False, f"路径不是有效目录: {path}"
        if not os.access(path, os.R_OK):
            return False, f"目录不可读: {path}"
        return True, ""
    
    @staticmethod
    def validate_file(path: str) -> Tuple[bool, str]:
        """验证文件是否存在且可访问"""
        if not path:
            return False, "文件路径不能为空"
        if not os.path.exists(path):
            return False, f"文件不存在: {path}"
        if not os.path.isfile(path):
            return False, f"路径不是有效文件: {path}"
        if not os.access(path, os.R_OK):
            return False, f"文件不可读: {path}"
        return True, ""
    
    @staticmethod
    def validate_writable_directory(path: str) -> Tuple[bool, str]:
        """验证目录是否可写"""
        valid, msg = Validator.validate_directory(path)
        if not valid:
            return valid, msg
        
        if not os.access(path, os.W_OK):
            return False, f"目录不可写: {path}"
        return True, ""
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "值") -> Tuple[bool, str]:
        """验证是否为正数"""
        try:
            num = float(value)
            if num <= 0:
                return False, f"{field_name}必须大于0"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}必须是有效的数字"
    
    @staticmethod
    def validate_non_negative_number(value: Any, field_name: str = "值") -> Tuple[bool, str]:
        """验证是否为非负数"""
        try:
            num = float(value)
            if num < 0:
                return False, f"{field_name}不能为负数"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}必须是有效的数字"
    
    @staticmethod
    def validate_range(value: Any, min_val: float, max_val: float, field_name: str = "值") -> Tuple[bool, str]:
        """验证数值是否在指定范围内"""
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return False, f"{field_name}必须在{min_val}和{max_val}之间"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}必须是有效的数字"
    
    @staticmethod
    def validate_extension(filename: str, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """验证文件扩展名"""
        ext = Path(filename).suffix.lower()
        allowed = [e.lower() if e.startswith('.') else f".{e.lower()}" for e in allowed_extensions]
        if ext not in allowed:
            return False, f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
        return True, ""
    
    @staticmethod
    def validate_video_file(path: str) -> Tuple[bool, str]:
        """验证是否为视频文件"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg']
        return Validator.validate_extension(path, video_extensions)
