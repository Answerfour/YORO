"""Unit tests for YOLO Trainer module"""
import unittest
import os
import tempfile
from modules.yolo_trainer.trainer import YOLOTrainer


class TestYOLOTrainer(unittest.TestCase):
    """Test cases for YOLOTrainer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.trainer = YOLOTrainer()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_cuda_available(self):
        """Test CUDA availability detection"""
        result = self.trainer.is_cuda_available()
        self.assertIsInstance(result, bool)

    def test_get_device_info(self):
        """Test device information retrieval"""
        info = self.trainer.get_device_info()
        self.assertIsInstance(info, dict)
        self.assertIn('device_type', info)
        self.assertIn('name', info)
        self.assertIn('memory_gb', info)

    def test_validate_parameters_empty_model(self):
        """Test parameter validation with empty model path"""
        params = {
            'model': '',
            'data': 'data.yaml',
            'epochs': 100,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn("Model file path cannot be empty", errors)

    def test_validate_parameters_empty_data(self):
        """Test parameter validation with empty data path"""
        params = {
            'model': 'yolo12s.pt',
            'data': '',
            'epochs': 100,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertIn("Data config file path cannot be empty", errors)

    def test_validate_parameters_invalid_epochs(self):
        """Test parameter validation with invalid epochs"""
        params = {
            'model': 'yolo12s.pt',
            'data': 'data.yaml',
            'epochs': 0,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertTrue(any("Epochs must be between 1-1000" in e for e in errors))

    def test_validate_parameters_invalid_batch(self):
        """Test parameter validation with invalid batch size"""
        params = {
            'model': 'yolo12s.pt',
            'data': 'data.yaml',
            'epochs': 100,
            'batch': 0,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertTrue(any("Batch size must be between 1-256" in e for e in errors))

    def test_validate_parameters_invalid_imgsz(self):
        """Test parameter validation with invalid image size"""
        params = {
            'model': 'yolo12s.pt',
            'data': 'data.yaml',
            'epochs': 100,
            'batch': 24,
            'imgsz': 30,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertFalse(is_valid)
        self.assertTrue(any("Image size must be between 32-2048" in e for e in errors))

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters"""
        data_path = os.path.join(self.test_dir, 'data.yaml')
        with open(data_path, 'w') as f:
            f.write("path: ./\ntrain: images\nval: images\nnc: 1\nnames:\n  0: class1")
        
        params = {
            'model': 'yolo12s.pt',
            'data': data_path,
            'epochs': 100,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test_run',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        is_valid, errors = self.trainer.validate_parameters(params)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_build_training_args_auto_device(self):
        """Test building training arguments with auto device"""
        params = {
            'model': 'yolo12s.pt',
            'data': 'data.yaml',
            'epochs': 100,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'auto',
            'amp': True,
            'cache': False
        }
        args = self.trainer.build_training_args(params)
        self.assertIn('device', args)
        self.assertIn('data', args)
        self.assertIn('epochs', args)
        self.assertIn('batch', args)
        self.assertIn('imgsz', args)

    def test_build_training_args_cpu_device(self):
        """Test building training arguments with cpu device"""
        params = {
            'model': 'yolo12s.pt',
            'data': 'data.yaml',
            'epochs': 100,
            'batch': 24,
            'imgsz': 640,
            'workers': 8,
            'project': 'output',
            'name': 'test',
            'device': 'cpu',
            'amp': True,
            'cache': False
        }
        args = self.trainer.build_training_args(params)
        self.assertEqual(args['device'], 'cpu')

    def test_create_data_yaml_empty_class_names(self):
        """Test creating data.yaml with empty class names"""
        yaml_content = self.trainer.create_data_yaml(self.test_dir)
        self.assertIsInstance(yaml_content, str)
        self.assertIn('path:', yaml_content)
        self.assertIn('train:', yaml_content)
        self.assertIn('val:', yaml_content)
        self.assertIn('nc:', yaml_content)
        self.assertIn('names:', yaml_content)

    def test_create_data_yaml_with_class_names(self):
        """Test creating data.yaml with explicit class names"""
        yaml_content = self.trainer.create_data_yaml(self.test_dir, ['cat', 'dog', 'car'])
        self.assertIsInstance(yaml_content, str)
        self.assertIn('nc: 3', yaml_content)
        self.assertIn('0: cat', yaml_content)
        self.assertIn('1: dog', yaml_content)
        self.assertIn('2: car', yaml_content)

    def test_save_data_yaml(self):
        """Test saving data.yaml to file"""
        yaml_content = self.trainer.create_data_yaml(self.test_dir)
        save_path = os.path.join(self.test_dir, 'data.yaml')
        success = self.trainer.save_data_yaml(yaml_content, save_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(save_path))

    def test_register_callback(self):
        """Test registering and triggering callbacks"""
        messages = []
        def callback(msg):
            messages.append(msg)
        
        self.trainer.register_callback(callback)
        self.trainer._notify("test message")
        
        self.assertIn("test message", messages)

    def test_save_data_yaml_failure(self):
        """Test saving data.yaml to invalid path"""
        yaml_content = "test: content"
        save_path = os.path.join(self.test_dir, 'nonexistent', 'data.yaml')
        success = self.trainer.save_data_yaml(yaml_content, save_path)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
