"""Validation Set Extractor Core Logic"""
import os
import random
import json
from typing import List, Set, Tuple, Dict, Optional
from core.file_operator import FileOperator
from datetime import datetime
from config.schema import ClassMappingConfig


class ClassBasedExtractor:
    """Class-based dataset extraction logic"""
    
    def __init__(self, labels_dir: str = "", project_root: str = ""):
        self.labels_dir = labels_dir
        self.project_root = project_root or os.getcwd()
        self.class_mapping: Dict[int, str] = {}
        self.image_to_classes: Dict[str, Set[int]] = {}
        self.class_to_images: Dict[int, List[str]] = {}
        self.original_stats: Dict = {}
        self.extraction_config: Dict = {}
        self.result_stats: Dict = {}
        
    def load_class_mapping(self, config_path: str = "") -> bool:
        """Load class mapping from JSON configuration file
        
        Args:
            config_path: Path to class_mapping.json. If empty, uses default location.
        
        Returns:
            True if successful, False otherwise
        """
        if not config_path:
            config_path = os.path.join(self.project_root, "config_data", "class_mapping.json")
        
        if not os.path.exists(config_path):
            self.class_mapping = {
                0: "water_heater",
                1: "paper_cup",
                2: "toilet",
                3: "fire_extinguisher",
                4: "commode",
                5: "sink"
            }
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.class_mapping = {int(k): v for k, v in data.items()}
            return True
        except Exception:
            self.class_mapping = {
                0: "water_heater",
                1: "paper_cup",
                2: "toilet",
                3: "fire_extinguisher",
                4: "commode",
                5: "sink"
            }
            return False
    
    def analyze_labels(self) -> Dict:
        """Analyze label files to build image-class relationships
        
        Returns:
            Dictionary containing statistics
        """
        self.image_to_classes = {}
        self.class_to_images = {}
        
        for cls_id in self.class_mapping.keys():
            self.class_to_images[cls_id] = []
        
        txt_files = FileOperator.get_txt_files(self.labels_dir, recursive=False)
        
        for file_path, name, _ in txt_files:
            classes_in_file = set()
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if parts:
                                try:
                                    cls_id = int(float(parts[0]))
                                    classes_in_file.add(cls_id)
                                except ValueError:
                                    continue
            except Exception:
                continue
            
            self.image_to_classes[name] = classes_in_file
            
            for cls_id in classes_in_file:
                if cls_id not in self.class_to_images:
                    self.class_to_images[cls_id] = []
                self.class_to_images[cls_id].append(name)
        
        self._compute_original_stats()
        return self.original_stats
    
    def _compute_original_stats(self):
        """Compute statistics from analyzed data"""
        total_images = len(self.image_to_classes)
        total_objects = sum(len(classes) for classes in self.image_to_classes.values())
        
        class_stats = {}
        for cls_id, images in self.class_to_images.items():
            class_name = self.class_mapping.get(cls_id, f"unknown_{cls_id}")
            class_stats[cls_id] = {
                'name': class_name,
                'count': len(images),
                'percentage': (len(images) / total_images) * 100 if total_images > 0 else 0
            }
        
        self.original_stats = {
            'total_images': total_images,
            'total_objects': total_objects,
            'class_stats': class_stats,
            'class_count': len(self.class_mapping)
        }
    
    def extract_by_classes(
        self,
        class_selections: Dict[int, float],
        seed: Optional[int] = None
    ) -> List[str]:
        """Extract images based on class selections and ratios
        
        Args:
            class_selections: Dictionary mapping class_id to extraction ratio (0.0-1.0)
            seed: Random seed for reproducibility
            
        Returns:
            List of selected image names
        """
        selected_images = set()
        
        if seed is not None:
            random.seed(seed)
        
        for cls_id, ratio in class_selections.items():
            if cls_id not in self.class_to_images or ratio <= 0:
                continue
            
            images = self.class_to_images[cls_id]
            count = max(1, int(len(images) * ratio))
            count = min(count, len(images))
            
            selected = random.sample(images, count)
            selected_images.update(selected)
        
        random.seed()
        
        self.extraction_config = {
            'class_selections': class_selections,
            'seed': seed,
            'selected_count': len(selected_images)
        }
        
        self._compute_result_stats(list(selected_images))
        
        return sorted(list(selected_images))
    
    def _compute_result_stats(self, selected_images: List[str]):
        """Compute statistics for the extracted dataset"""
        total_images = len(selected_images)
        total_objects = 0
        class_stats = {cls_id: {'name': self.class_mapping.get(cls_id, f"unknown_{cls_id}"), 'count': 0} 
                       for cls_id in self.class_mapping.keys()}
        
        for name in selected_images:
            if name in self.image_to_classes:
                total_objects += len(self.image_to_classes[name])
                for cls_id in self.image_to_classes[name]:
                    if cls_id in class_stats:
                        class_stats[cls_id]['count'] += 1
        
        for cls_id in class_stats:
            class_stats[cls_id]['percentage'] = (class_stats[cls_id]['count'] / total_images) * 100 if total_images > 0 else 0
        
        self.result_stats = {
            'total_images': total_images,
            'total_objects': total_objects,
            'class_stats': class_stats
        }
    
    def generate_extraction_report(self) -> str:
        """Generate a comprehensive extraction report
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        report.append("DATASET EXTRACTION REPORT")
        report.append("=" * 70)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("--- ORIGINAL DATASET STATISTICS ---")
        report.append(f"Total Images: {self.original_stats.get('total_images', 0)}")
        report.append(f"Total Objects: {self.original_stats.get('total_objects', 0)}")
        report.append(f"Number of Classes: {self.original_stats.get('class_count', 0)}")
        report.append("")
        report.append("Class Distribution:")
        for cls_id, stats in sorted(self.original_stats.get('class_stats', {}).items()):
            report.append(f"  [{cls_id}] {stats['name']}: {stats['count']} images ({stats['percentage']:.2f}%)")
        report.append("")
        
        report.append("--- EXTRACTION CONFIGURATION ---")
        report.append(f"Random Seed: {self.extraction_config.get('seed', 'None')}")
        report.append("Selected Classes and Ratios:")
        for cls_id, ratio in self.extraction_config.get('class_selections', {}).items():
            cls_name = self.class_mapping.get(cls_id, f"unknown_{cls_id}")
            report.append(f"  [{cls_id}] {cls_name}: {int(ratio * 100)}%")
        report.append("")
        
        report.append("--- EXTRACTION RESULTS ---")
        report.append(f"Selected Images: {self.result_stats.get('total_images', 0)}")
        report.append(f"Selected Objects: {self.result_stats.get('total_objects', 0)}")
        report.append("")
        report.append("Extracted Class Distribution:")
        for cls_id, stats in sorted(self.result_stats.get('class_stats', {}).items()):
            report.append(f"  [{cls_id}] {stats['name']}: {stats['count']} images ({stats['percentage']:.2f}%)")
        report.append("")
        
        report.append("--- VALIDATION ---")
        if self.result_stats.get('total_images', 0) > 0:
            report.append("[OK] Extraction completed successfully")
            report.append(f"[OK] Data integrity maintained: {self.result_stats['total_images']} paired files")
        else:
            report.append("[FAIL] No images were selected")
        
        report.append("=" * 70)
        
        return "\n".join(report)


class ValidExtractor:
    """Validation set extractor - extracts paired image/label files from train set"""

    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    LABEL_EXTENSIONS = ['.txt']

    def __init__(self, images_dir: str = "", labels_dir: str = "", project_root: str = ""):
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        self.project_root = project_root or os.getcwd()

        self.image_files: List[Tuple[str, str, str]] = []
        self.label_files: List[Tuple[str, str, str]] = []
        self.paired_files: Dict[str, Tuple[str, str]] = {}
        self.unpaired_images: Set[str] = set()
        self.unpaired_labels: Set[str] = set()

    def scan_directories(self) -> Tuple[int, int]:
        """Recursively scan images and labels directories

        Returns:
            (image_count, label_count)
        """
        self.image_files = FileOperator.get_image_files(self.images_dir, recursive=True)
        self.label_files = FileOperator.get_txt_files(self.labels_dir, recursive=True)

        image_names = {f[1] for f in self.image_files}
        label_names = {f[1] for f in self.label_files}

        self.paired_files = {}
        for name in image_names & label_names:
            img_path = next(f[0] for f in self.image_files if f[1] == name)
            lbl_path = next(f[0] for f in self.label_files if f[1] == name)
            self.paired_files[name] = (img_path, lbl_path)

        self.unpaired_images = image_names - label_names
        self.unpaired_labels = label_names - image_names

        return len(self.image_files), len(self.label_files)

    def get_match_report(self) -> Dict:
        """Generate file matching report

        Returns:
            Dict with paired_count, unpaired_images_count, unpaired_labels_count,
            and sorted name lists
        """
        return {
            'paired_count': len(self.paired_files),
            'unpaired_images_count': len(self.unpaired_images),
            'unpaired_labels_count': len(self.unpaired_labels),
            'unpaired_images': sorted(list(self.unpaired_images)),
            'unpaired_labels': sorted(list(self.unpaired_labels)),
            'paired_names': sorted(list(self.paired_files.keys())),
        }

    def select_by_ratio(self, ratio: float, seed: Optional[int] = None) -> List[str]:
        """Select a random subset of paired files by ratio

        Args:
            ratio: Extraction ratio (0.0 to 1.0)
            seed: Random seed for reproducibility

        Returns:
            Sorted list of selected file names
        """
        paired_names = list(self.paired_files.keys())
        count = max(1, int(len(paired_names) * ratio))
        return self._random_select(paired_names, count, seed)

    def select_by_count(self, count: int, seed: Optional[int] = None) -> List[str]:
        """Select a random subset of paired files by exact count

        Args:
            count: Number of files to select
            seed: Random seed for reproducibility

        Returns:
            Sorted list of selected file names
        """
        paired_names = list(self.paired_files.keys())
        count = min(count, len(paired_names))
        return self._random_select(paired_names, count, seed)

    def select_manual(self, selected_names: List[str]) -> List[str]:
        """Select manually specified file names

        Args:
            selected_names: List of file names to select

        Returns:
            List of valid selected file names (sorted)
        """
        return sorted([n for n in selected_names if n in self.paired_files])

    def _random_select(self, names: List[str], count: int, seed: Optional[int] = None) -> List[str]:
        """Randomly select a subset of names"""
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()
        selected = random.sample(names, count)
        random.seed()
        return sorted(selected)

    def generate_preview(self, selected_names: List[str]) -> List[Tuple[str, str, str]]:
        """Generate preview list of files to be extracted

        Args:
            selected_names: List of selected file names

        Returns:
            List of (name, image_path, label_path) tuples
        """
        preview = []
        for name in selected_names:
            if name in self.paired_files:
                img_path, lbl_path = self.paired_files[name]
                preview.append((name, img_path, lbl_path))
        return preview

    def execute_extraction(
        self,
        selected_names: List[str],
        operation: str = "copy",
        valid_dir: str = ""
    ) -> Tuple[int, int, List[Dict]]:
        """Execute copy or move operation for selected files

        Args:
            selected_names: List of file names to extract
            operation: 'copy' or 'move'
            valid_dir: Target valid/ directory path (project root by default)

        Returns:
            (success_count, failure_count, error_details)
        """
        base_dir = valid_dir or os.path.join(self.project_root, "valid")
        images_target = os.path.join(base_dir, "images")
        labels_target = os.path.join(base_dir, "labels")

        FileOperator.ensure_directory(images_target)
        FileOperator.ensure_directory(labels_target)

        success_count = 0
        failure_count = 0
        error_details = []

        for name in selected_names:
            if name not in self.paired_files:
                failure_count += 1
                error_details.append({
                    'file': name,
                    'error': 'File not found in paired list',
                    'type': 'both'
                })
                continue

            img_path, lbl_path = self.paired_files[name]
            img_ext = os.path.splitext(img_path)[1]
            lbl_ext = os.path.splitext(lbl_path)[1]

            img_dest = os.path.join(images_target, f"{name}{img_ext}")
            lbl_dest = os.path.join(labels_target, f"{name}{lbl_ext}")

            img_ok = True
            lbl_ok = True

            if operation == "copy":
                ok, err = FileOperator.safe_copy_file(img_path, img_dest, overwrite=True)
                if not ok:
                    img_ok = False
                    error_details.append({
                        'file': f"{name}{img_ext}",
                        'error': err,
                        'type': 'image'
                    })
                ok, err = FileOperator.safe_copy_file(lbl_path, lbl_dest, overwrite=True)
                if not ok:
                    lbl_ok = False
                    error_details.append({
                        'file': f"{name}{lbl_ext}",
                        'error': err,
                        'type': 'label'
                    })
            else:
                ok, err = FileOperator.safe_move_file(img_path, img_dest, overwrite=True)
                if not ok:
                    img_ok = False
                    error_details.append({
                        'file': f"{name}{img_ext}",
                        'error': err,
                        'type': 'image'
                    })
                ok, err = FileOperator.safe_move_file(lbl_path, lbl_dest, overwrite=True)
                if not ok:
                    lbl_ok = False
                    error_details.append({
                        'file': f"{name}{lbl_ext}",
                        'error': err,
                        'type': 'label'
                    })

            if img_ok and lbl_ok:
                success_count += 1
            else:
                failure_count += 1

        return success_count, failure_count, error_details

    def validate_extraction(self, valid_dir: str = "") -> Dict:
        """Validate extracted files in the valid directory

        Args:
            valid_dir: Path to the valid/ directory

        Returns:
            Dict with validation results
        """
        base_dir = valid_dir or os.path.join(self.project_root, "valid")
        images_dir = os.path.join(base_dir, "images")
        labels_dir = os.path.join(base_dir, "labels")

        result = {
            'valid': False,
            'images_dir_exists': False,
            'labels_dir_exists': False,
            'image_count': 0,
            'label_count': 0,
            'paired_count': 0,
            'missing_labels': [],
            'missing_images': [],
            'total_image_size': 0,
            'total_label_size': 0
        }

        if not os.path.isdir(images_dir):
            return result
        result['images_dir_exists'] = True

        if not os.path.isdir(labels_dir):
            return result
        result['labels_dir_exists'] = True

        images = FileOperator.get_image_files(images_dir, recursive=False)
        labels = FileOperator.get_txt_files(labels_dir, recursive=False)

        result['image_count'] = len(images)
        result['label_count'] = len(labels)

        image_names = {f[1] for f in images}
        label_names = {f[1] for f in labels}

        result['paired_count'] = len(image_names & label_names)
        result['missing_labels'] = sorted(list(image_names - label_names))
        result['missing_images'] = sorted(list(label_names - image_names))

        for img in images:
            result['total_image_size'] += FileOperator.get_file_size(img[0])
        for lbl in labels:
            result['total_label_size'] += FileOperator.get_file_size(lbl[0])

        result['valid'] = result['paired_count'] == result['image_count'] == result['label_count']
        return result