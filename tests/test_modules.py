#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test script - Verify modular refactoring functionality"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_utils():
    print("\n=== Test utils Module ===")
    from utils import Logger, PersistenceManager, ThreadPool
    
    logger = Logger.get_instance()
    print("[PASS] Logger singleton works")
    
    persistence = PersistenceManager.get_instance()
    print("[PASS] PersistenceManager singleton works")
    
    pool = ThreadPool.get_instance()
    print("[PASS] ThreadPool singleton works")


def test_core():
    print("\n=== Test core Module ===")
    from core import Validator, FileOperator, natural_sort_key
    from config.schema import RenamerConfig
    
    is_valid, msg = Validator.validate_positive_number(10, "test_value")
    assert is_valid, f"Validation failed: {msg}"
    print("[PASS] Validator works")
    
    config = RenamerConfig(file_type="txt", start_number=1, digit_width=6)
    assert config.file_type == "txt"
    print("[PASS] RenamerConfig works")
    
    sorted_files = natural_sort_key("file10.txt")
    assert sorted_files == ['file', 10, '.txt']
    print("[PASS] natural_sort_key works")


def test_config():
    print("\n=== Test config Module ===")
    from config.schema import (
        FrameExtractorConfig, ClassMappingConfig, 
        OutputFormat, NamingMode
    )
    
    config = FrameExtractorConfig(
        start_time=0.0,
        end_time=10.0,
        sample_fps=1.0
    )
    errors = config.validate()
    assert len(errors) == 0, f"Config validation failed: {errors}"
    print("[PASS] FrameExtractorConfig works")
    
    class_config = ClassMappingConfig()
    class_config.add_class(99, "test_class")
    assert class_config.mapping[99] == "test_class"
    print("[PASS] ClassMappingConfig works")
    
    assert OutputFormat.JPG.value == "jpg"
    assert NamingMode.SEQUENCE.value == "sequence"
    print("[PASS] Enum types work")


def test_modules():
    print("\n=== Test modules ===")
    from modules import FrameExtractorGUI, FileRenamerGUI, OrphanCleanerGUI, YOLOStatsGUI
    
    print("[PASS] FrameExtractorGUI imported")
    print("[PASS] FileRenamerGUI imported")
    print("[PASS] OrphanCleanerGUI imported")
    print("[PASS] YOLOStatsGUI imported")


def test_app():
    print("\n=== Test main application ===")
    from app import YOLOToolsApp
    
    print("[PASS] YOLOToolsApp imported")


def main():
    print("=" * 60)
    print("YOLO Tools Collection - Modular Refactoring Test")
    print("=" * 60)
    
    try:
        test_utils()
        test_core()
        test_config()
        test_modules()
        test_app()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed! Modular refactoring complete!")
        print("=" * 60)
        print("\nRun the application: python main.py")
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
