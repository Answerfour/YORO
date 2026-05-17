"""Data Validators - Provide input validation functions"""
import os
from typing import List, Tuple, Any
from pathlib import Path


class Validator:
    """General purpose validator"""
    
    @staticmethod
    def validate_directory(path: str) -> Tuple[bool, str]:
        """Validate if directory exists and is accessible"""
        if not path:
            return False, "Directory path cannot be empty"
        if not os.path.exists(path):
            return False, f"Directory does not exist: {path}"
        if not os.path.isdir(path):
            return False, f"Path is not a valid directory: {path}"
        if not os.access(path, os.R_OK):
            return False, f"Directory is not readable: {path}"
        return True, ""
    
    @staticmethod
    def validate_file(path: str) -> Tuple[bool, str]:
        """Validate if file exists and is accessible"""
        if not path:
            return False, "File path cannot be empty"
        if not os.path.exists(path):
            return False, f"File does not exist: {path}"
        if not os.path.isfile(path):
            return False, f"Path is not a valid file: {path}"
        if not os.access(path, os.R_OK):
            return False, f"File is not readable: {path}"
        return True, ""
    
    @staticmethod
    def validate_writable_directory(path: str) -> Tuple[bool, str]:
        """Validate if directory is writable"""
        valid, msg = Validator.validate_directory(path)
        if not valid:
            return valid, msg
        
        if not os.access(path, os.W_OK):
            return False, f"Directory is not writable: {path}"
        return True, ""
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "value") -> Tuple[bool, str]:
        """Validate if value is a positive number"""
        try:
            num = float(value)
            if num <= 0:
                return False, f"{field_name} must be greater than 0"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_non_negative_number(value: Any, field_name: str = "value") -> Tuple[bool, str]:
        """Validate if value is a non-negative number"""
        try:
            num = float(value)
            if num < 0:
                return False, f"{field_name} cannot be negative"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_range(value: Any, min_val: float, max_val: float, field_name: str = "value") -> Tuple[bool, str]:
        """Validate if value is within specified range"""
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return False, f"{field_name} must be between {min_val} and {max_val}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_extension(filename: str, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """Validate file extension"""
        ext = Path(filename).suffix.lower()
        allowed = [e.lower() if e.startswith('.') else f".{e.lower()}" for e in allowed_extensions]
        if ext not in allowed:
            return False, f"Unsupported file type. Supported: {', '.join(allowed_extensions)}"
        return True, ""
    
    @staticmethod
    def validate_video_file(path: str) -> Tuple[bool, str]:
        """Validate if file is a video file"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg']
        return Validator.validate_extension(path, video_extensions)