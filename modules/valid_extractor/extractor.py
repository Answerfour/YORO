"""Validation Set Extractor Core Logic"""
import os
import random
from typing import List, Set, Tuple, Dict, Optional
from core.file_operator import FileOperator
from datetime import datetime


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