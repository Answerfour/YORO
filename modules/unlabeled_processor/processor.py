"""Unlabeled File Processor Core Logic"""
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from pathlib import Path


class UnlabeledProcessor:
    """Process images and label files without annotation information"""
    
    def __init__(self, main_folder: str):
        self.main_folder = main_folder
        self.images_folder = os.path.join(main_folder, "images")
        self.labels_folder = os.path.join(main_folder, "labels")
        self.unlabeled_folder = os.path.join(main_folder, "unlabeled_files")
        
        self.empty_labels: List[str] = []
        self.matched_images: List[str] = []
        self.processed_count = 0
        self.failed_count = 0
        self.logs: List[str] = []
        
        self._cancelled = False
    
    def validate_folders(self) -> Tuple[bool, str]:
        """Validate folder structure"""
        if not os.path.exists(self.main_folder):
            return False, f"Main folder does not exist: {self.main_folder}"
        
        if not os.path.exists(self.images_folder):
            return False, f"images folder does not exist: {self.images_folder}"
        
        if not os.path.exists(self.labels_folder):
            return False, f"labels folder does not exist: {self.labels_folder}"
        
        return True, ""
    
    def find_empty_labels(self) -> List[str]:
        """Find all empty label files"""
        empty_labels = []
        
        if not os.path.exists(self.labels_folder):
            return empty_labels
        
        for filename in os.listdir(self.labels_folder):
            if filename.lower().endswith('.txt'):
                filepath = os.path.join(self.labels_folder, filename)
                if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
                    empty_labels.append(filename)
        
        self.empty_labels = empty_labels
        return empty_labels
    
    def find_matched_images(self, label_filename: str) -> Optional[str]:
        """Find images corresponding to label files"""
        base_name = os.path.splitext(label_filename)[0]
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        for ext in image_extensions:
            image_path = os.path.join(self.images_folder, base_name + ext)
            if os.path.exists(image_path):
                return image_path
        
        return None
    
    def get_all_matched_pairs(self) -> List[Tuple[str, str]]:
        """Get all pairs of empty labels and their corresponding images"""
        pairs = []
        for label_file in self.empty_labels:
            image_path = self.find_matched_images(label_file)
            if image_path:
                pairs.append((label_file, image_path))
            else:
                self.logs.append(f"Warning: No matching image found for label {label_file}")
        
        return pairs
    
    def process_move(self) -> Tuple[int, int, List[str]]:
        """Move mode: Move empty labels and corresponding images to unlabeled_files directory"""
        os.makedirs(self.unlabeled_folder, exist_ok=True)
        images_dest = os.path.join(self.unlabeled_folder, "images")
        labels_dest = os.path.join(self.unlabeled_folder, "labels")
        os.makedirs(images_dest, exist_ok=True)
        os.makedirs(labels_dest, exist_ok=True)
        
        processed = 0
        failed = 0
        logs = []
        
        for label_file in self.empty_labels:
            if self._cancelled:
                logs.append("Operation cancelled")
                break
            
            label_path = os.path.join(self.labels_folder, label_file)
            image_path = self.find_matched_images(label_file)
            
            try:
                dest_label = os.path.join(labels_dest, label_file)
                shutil.move(label_path, dest_label)
                logs.append(f"Moved label: {label_file}")
                
                if image_path:
                    dest_image = os.path.join(images_dest, os.path.basename(image_path))
                    shutil.move(image_path, dest_image)
                    logs.append(f"Moved image: {os.path.basename(image_path)}")
                
                processed += 1
            except Exception as e:
                logs.append(f"Failed to move {label_file}: {str(e)}")
                failed += 1
        
        return processed, failed, logs
    
    def process_delete(self) -> Tuple[int, int, List[str]]:
        """Delete mode: Delete empty labels and corresponding images directly"""
        processed = 0
        failed = 0
        logs = []
        
        for label_file in self.empty_labels:
            if self._cancelled:
                logs.append("Operation cancelled")
                break
            
            label_path = os.path.join(self.labels_folder, label_file)
            image_path = self.find_matched_images(label_file)
            
            try:
                os.remove(label_path)
                logs.append(f"Deleted label: {label_file}")
                
                if image_path:
                    os.remove(image_path)
                    logs.append(f"Deleted image: {os.path.basename(image_path)}")
                
                processed += 1
            except Exception as e:
                logs.append(f"Failed to delete {label_file}: {str(e)}")
                failed += 1
        
        return processed, failed, logs
    
    def cancel(self):
        """Cancel operation"""
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
    
    def generate_report(self, processed: int, failed: int) -> str:
        """Generate processing report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = [
            f"Processing time: {timestamp}",
            f"Main folder: {self.main_folder}",
            f"Empty label files: {len(self.empty_labels)}",
            f"Successfully processed: {processed}",
            f"Failed: {failed}",
            "=" * 50,
            "Operation log:"
        ]
        report.extend(self.logs)
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = None):
        """Save processing report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unlabeled_report_{timestamp}.txt"
        
        report_path = os.path.join(self.main_folder, filename)
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            return True, report_path
        except Exception as e:
            return False, str(e)