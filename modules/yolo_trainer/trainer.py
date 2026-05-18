"""YOLO Training Core Logic"""
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False


class YOLOTrainer:
    """YOLO Model Trainer - Handles training configuration and execution"""

    def __init__(self):
        self.model = None
        self.is_training = False
        self._training_callbacks = []

    def register_callback(self, callback):
        """Register a callback for training events
        
        Args:
            callback: Function to be called with training events
        """
        self._training_callbacks.append(callback)

    def _notify(self, message: str):
        """Notify all registered callbacks with a message"""
        for callback in self._training_callbacks:
            callback(message)

    def is_cuda_available(self) -> bool:
        """Check if CUDA is available
        
        Returns:
            True if CUDA is available, False otherwise
        """
        if not TORCH_AVAILABLE:
            return False
        return torch.cuda.is_available()

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information
        
        Returns:
            Dictionary containing device name and memory information
        """
        if TORCH_AVAILABLE and torch.cuda.is_available():
            return {
                'device_type': 'cuda',
                'name': torch.cuda.get_device_name(0),
                'memory_gb': torch.cuda.get_device_properties(0).total_memory / 1e9
            }
        return {
            'device_type': 'cpu',
            'name': 'CPU',
            'memory_gb': 0.0
        }

    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate training parameters
        
        Args:
            params: Dictionary containing training parameters
            
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []

        model_path = params.get('model', '').strip()
        if not model_path:
            errors.append("Model file path cannot be empty")

        data_path = params.get('data', '').strip()
        if not data_path:
            errors.append("Data config file path cannot be empty")
        elif not os.path.exists(data_path):
            errors.append(f"Data config file does not exist: {data_path}")

        epochs = params.get('epochs', 100)
        if epochs < 1 or epochs > 1000:
            errors.append(f"Epochs must be between 1-1000, current: {epochs}")

        batch = params.get('batch', 24)
        if batch < 1 or batch > 256:
            errors.append(f"Batch size must be between 1-256, current: {batch}")

        imgsz = params.get('imgsz', 640)
        if imgsz < 32 or imgsz > 2048:
            errors.append(f"Image size must be between 32-2048, current: {imgsz}")

        workers = params.get('workers', 8)
        if workers < 0 or workers > 64:
            errors.append(f"Workers must be between 0-64, current: {workers}")

        project = params.get('project', '').strip()
        if not project:
            errors.append("Output directory cannot be empty")

        name = params.get('name', '').strip()
        if not name:
            errors.append("Run name cannot be empty")
        elif not name.replace("_", "").replace("-", "").isalnum():
            errors.append("Run name can only contain alphanumeric characters, underscores, and hyphens")

        return (len(errors) == 0, errors)

    def build_training_args(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build training arguments for YOLO model
        
        Args:
            params: Dictionary containing training parameters
            
        Returns:
            Dictionary of training arguments
        """
        resolved_device = params['device']
        if params['device'] == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                resolved_device = "cuda"
            else:
                resolved_device = "cpu"
        elif params['device'] == "cuda" and not (TORCH_AVAILABLE and torch.cuda.is_available()):
            resolved_device = "cpu"

        workers_val = min(params['workers'], os.cpu_count() or 1)

        return {
            'data': params['data'],
            'epochs': params['epochs'],
            'batch': params['batch'],
            'imgsz': params['imgsz'],
            'amp': params['amp'],
            'cache': params['cache'],
            'device': resolved_device,
            'workers': workers_val,
            'project': params['project'],
            'name': params['name'],
            'verbose': True,
            'resume': params.get('resume', False)
        }

    def create_data_yaml(self, dataset_path: str, class_names: Optional[List[str]] = None) -> str:
        """Create a data.yaml file for YOLO training
        
        Args:
            dataset_path: Path to the dataset root directory
            class_names: Optional list of class names
            
        Returns:
            Generated YAML content as string
        """
        if class_names is None:
            class_names = []
            label_dir = os.path.join(dataset_path, "labels")
            if os.path.exists(label_dir):
                for f in os.listdir(label_dir):
                    if f.endswith(".txt"):
                        with open(os.path.join(label_dir, f), 'r') as lf:
                            for line in lf:
                                cls_id = line.strip().split()[0] if line.strip() else None
                                if cls_id and cls_id not in class_names:
                                    class_names.append(cls_id)

        if not class_names:
            class_names = [str(i) for i in range(80)]

        yaml_content = f"path: {os.path.abspath(dataset_path)}\n"
        yaml_content += "train: images\n"
        yaml_content += "val: images\n\n"
        yaml_content += f"nc: {len(class_names)}\n"
        yaml_content += "names:\n"
        for i, name in enumerate(class_names):
            yaml_content += f"  {i}: {name}\n"

        return yaml_content

    def save_data_yaml(self, yaml_content: str, save_path: str) -> bool:
        """Save YAML content to file
        
        Args:
            yaml_content: YAML content string
            save_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            return True
        except Exception:
            return False

    def train(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute YOLO model training
        
        Args:
            params: Dictionary containing training parameters
            
        Returns:
            Dictionary with training results
        """
        self.is_training = True
        results = {
            'success': False,
            'message': '',
            'elapsed_time': 0,
            'output_dir': '',
            'error': None
        }

        if not TORCH_AVAILABLE:
            results['error'] = "PyTorch is not available. Please install torch and ultralytics."
            results['message'] = "Training failed: PyTorch not installed"
            self.is_training = False
            return results

        try:
            from ultralytics import YOLO

            self._notify("Initializing training environment...")

            args = self.build_training_args(params)
            
            self._notify(f"Auto-selected device: {args['device']}")
            if args['device'] == "cuda":
                self._notify(f"GPU: {torch.cuda.get_device_name(0)}")
                mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                self._notify(f"GPU Memory: {mem:.1f} GB")
            else:
                self._notify("Using CPU training")

            self._notify(f"Loading model: {params['model']}")
            model = YOLO(params['model'])

            if args['workers'] != params['workers']:
                self._notify(f"Workers adjusted to: {args['workers']} (CPU core limit)")

            self._notify(f"Data config: {params['data']}")
            self._notify(f"Training epochs: {params['epochs']}")
            self._notify(f"Batch size: {params['batch']}")
            self._notify(f"Image size: {params['imgsz']}")
            self._notify(f"Output directory: {params['project']}/{params['name']}")
            self._notify("Starting model training...")

            start_time = time.time()

            model.train(**args)

            elapsed = time.time() - start_time
            results['elapsed_time'] = elapsed
            results['output_dir'] = os.path.join(params['project'], params['name'])
            results['success'] = True

            self._notify(f"Training completed! Time: {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)")
            self._notify(f"Model saved to: {results['output_dir']}/")

            results_csv = os.path.join(results['output_dir'], "results.csv")
            if os.path.exists(results_csv):
                self._notify("Generating training results plot...")
                try:
                    from ultralytics.utils.plotting import plot_results
                    plot_results(file=results_csv)
                    self._notify("Training results plot generated")
                except Exception as e:
                    self._notify(f"Plot generation failed: {e}")
            else:
                self._notify(f"Results file not found: {results_csv}")

        except Exception as e:
            results['error'] = str(e)
            results['message'] = f"Training error: {e}"
            import traceback
            self._notify(f"Training error: {e}")
            self._notify(traceback.format_exc())
        finally:
            self.is_training = False

        return results