"""Unit tests for ValidExtractor module"""
import unittest
import os
import json
import tempfile
from modules.valid_extractor.extractor import ValidExtractor


class TestValidExtractor(unittest.TestCase):
    """Test cases for ValidExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.images_dir = os.path.join(self.temp_dir, "images")
        self.labels_dir = os.path.join(self.temp_dir, "labels")
        self.config_dir = os.path.join(self.temp_dir, "config_data")
        
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.class_mapping = {
            0: "water_heater",
            1: "paper_cup",
            2: "toilet"
        }
        
        class_mapping_path = os.path.join(self.config_dir, "class_mapping.json")
        with open(class_mapping_path, 'w', encoding='utf-8') as f:
            json.dump(self.class_mapping, f)
        
        for i in range(10):
            img_file = os.path.join(self.images_dir, f"image_{i}.jpg")
            with open(img_file, 'w') as f:
                f.write(f"dummy image {i}")
            
            if i < 4:
                label_content = f"0 0.5 0.5 0.5 0.5\n1 0.3 0.3 0.3 0.3\n"
            elif i < 7:
                label_content = f"1 0.5 0.5 0.5 0.5\n"
            else:
                label_content = f"2 0.5 0.5 0.5 0.5\n"
            
            label_file = os.path.join(self.labels_dir, f"image_{i}.txt")
            with open(label_file, 'w') as f:
                f.write(label_content)
        
        self.extractor = ValidExtractor(
            images_dir=self.images_dir,
            labels_dir=self.labels_dir,
            project_root=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_class_mapping(self):
        """Test loading class mapping from JSON file"""
        result = self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.assertTrue(result)
        self.assertEqual(self.extractor.class_mapping, self.class_mapping)
    
    def test_load_class_mapping_default(self):
        """Test loading default class mapping when file not found"""
        result = self.extractor.load_class_mapping("/nonexistent/path.json")
        self.assertFalse(result)
        self.assertIsInstance(self.extractor.class_mapping, dict)
        self.assertTrue(len(self.extractor.class_mapping) > 0)
    
    def test_scan_directories(self):
        """Test scanning image and label directories"""
        img_count, lbl_count = self.extractor.scan_directories()
        self.assertEqual(img_count, 10)
        self.assertEqual(lbl_count, 10)
        self.assertEqual(len(self.extractor.paired_files), 10)
    
    def test_analyze_labels(self):
        """Test analyzing label files for class distribution"""
        self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.extractor.scan_directories()
        stats = self.extractor.analyze_labels()
        
        self.assertEqual(stats['total_images'], 10)
        self.assertEqual(stats['class_count'], 3)
        
        class_stats = stats['class_stats']
        self.assertIn(0, class_stats)
        self.assertIn(1, class_stats)
        self.assertIn(2, class_stats)
        
        self.assertEqual(class_stats[0]['name'], 'water_heater')
        self.assertEqual(class_stats[0]['count'], 4)
        
        self.assertEqual(class_stats[1]['name'], 'paper_cup')
        self.assertEqual(class_stats[1]['count'], 7)
        
        self.assertEqual(class_stats[2]['name'], 'toilet')
        self.assertEqual(class_stats[2]['count'], 3)
    
    def test_validate_ratio(self):
        """Test ratio validation method"""
        self.assertTrue(ValidExtractor.validate_ratio(0.0))
        self.assertTrue(ValidExtractor.validate_ratio(0.5))
        self.assertTrue(ValidExtractor.validate_ratio(1.0))
        self.assertFalse(ValidExtractor.validate_ratio(-0.1))
        self.assertFalse(ValidExtractor.validate_ratio(1.1))
    
    def test_validate_class_selections(self):
        """Test class selection validation"""
        valid_selections = {0: 0.5, 1: 0.3}
        result, error = ValidExtractor.validate_class_selections(valid_selections)
        self.assertTrue(result)
        self.assertEqual(error, "")
        
        empty_selections = {}
        result, error = ValidExtractor.validate_class_selections(empty_selections)
        self.assertFalse(result)
        self.assertEqual(error, "No classes selected")
        
        invalid_ratio_selections = {0: 1.5}
        result, error = ValidExtractor.validate_class_selections(invalid_ratio_selections)
        self.assertFalse(result)
        self.assertIn("must be between", error)
        
        invalid_class_id_selections = {-1: 0.5}
        result, error = ValidExtractor.validate_class_selections(invalid_class_id_selections)
        self.assertFalse(result)
        self.assertIn("Invalid class ID", error)
    
    def test_extract_by_classes(self):
        """Test extracting images by class selections"""
        self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.extractor.scan_directories()
        self.extractor.analyze_labels()
        
        class_selections = {0: 0.5, 1: 0.5}
        selected, error = self.extractor.extract_by_classes(class_selections, seed=42)
        
        self.assertEqual(error, "")
        self.assertGreater(len(selected), 0)
        self.assertLessEqual(len(selected), 10)
        
        for name in selected:
            self.assertIn(name, self.extractor.paired_files)
    
    def test_extract_by_classes_with_invalid_input(self):
        """Test extraction with invalid inputs"""
        self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.extractor.scan_directories()
        self.extractor.analyze_labels()
        
        selected, error = self.extractor.extract_by_classes({}, seed=42)
        self.assertEqual(selected, [])
        self.assertIn("No classes selected", error)
        
        selected, error = self.extractor.extract_by_classes({0: 1.5}, seed=42)
        self.assertEqual(selected, [])
        self.assertIn("must be between", error)
    
    def test_extract_by_classes_reproducibility(self):
        """Test that extraction with same seed produces same results"""
        self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.extractor.scan_directories()
        self.extractor.analyze_labels()
        
        class_selections = {0: 0.5, 1: 0.5}
        
        selected1, _ = self.extractor.extract_by_classes(class_selections, seed=42)
        selected2, _ = self.extractor.extract_by_classes(class_selections, seed=42)
        
        self.assertEqual(selected1, selected2)
    
    def test_generate_extraction_report(self):
        """Test generating extraction report"""
        self.extractor.load_class_mapping(
            os.path.join(self.config_dir, "class_mapping.json")
        )
        self.extractor.scan_directories()
        self.extractor.analyze_labels()
        
        class_selections = {0: 0.5}
        self.extractor.extract_by_classes(class_selections, seed=42)
        
        report = self.extractor.generate_extraction_report()
        
        self.assertIsInstance(report, str)
        self.assertIn("DATASET EXTRACTION REPORT", report)
        self.assertIn("ORIGINAL DATASET STATISTICS", report)
        self.assertIn("EXTRACTION CONFIGURATION", report)
        self.assertIn("EXTRACTION RESULTS", report)
        self.assertIn("VALIDATION", report)


if __name__ == '__main__':
    unittest.main()