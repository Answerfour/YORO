"""YOLO Training Tools Collection - Main Application Entry"""
import tkinter as tk
from tkinter import ttk
from modules.frame_extractor.gui import FrameExtractorGUI
from modules.file_renamer.gui import FileRenamerGUI
from modules.orphan_cleaner.gui import OrphanCleanerGUI
from modules.yolo_stats.gui import YOLOStatsGUI
from modules.unlabeled_processor.gui import UnlabeledProcessorGUI
from modules.valid_extractor.gui import ValidExtractorGUI
from modules.yolo_trainer.gui import YOLOTrainerGUI
from ui.theme import Theme


class YOLOToolsApp:
    """YOLO Training Tools Collection Main Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YORO-You Only Run Once")
        self.root.geometry("1000x800")
        
        Theme.apply_default_style()
        
        self._create_menu()
        self._create_ui()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.frame_extractor = FrameExtractorGUI(notebook)
        notebook.add(self.frame_extractor, text="📹 Video Frame Extraction")
        
        self.file_renamer = FileRenamerGUI(notebook)
        notebook.add(self.file_renamer, text="📝 Batch Rename")
        
        self.orphan_cleaner = OrphanCleanerGUI(notebook)
        notebook.add(self.orphan_cleaner, text="🧹 Orphan File Cleaner")
        
        self.unlabeled_processor = UnlabeledProcessorGUI(notebook)
        notebook.add(self.unlabeled_processor, text="📋 Unlabeled Processor")
        
        self.yolo_stats = YOLOStatsGUI(notebook)
        notebook.add(self.yolo_stats, text="📊 YOLO Statistics")
        
        self.valid_extractor = ValidExtractorGUI(notebook)
        notebook.add(self.valid_extractor, text="✅ Validation Set Extractor")
        
        self.yolo_trainer = YOLOTrainerGUI(notebook)
        notebook.add(self.yolo_trainer, text="🚀 YOLO Trainer")
    
    def _show_about(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "About",
            "YOLO Training Tools Collection\n\n"
            "Version: 2.3 (Modular Refactored)\n\n"
            "Features:\n"
            "• Video Frame Extraction\n"
            "• Batch File Rename\n"
            "• Orphan File Cleaning\n"
            "• Unlabeled File Processing\n"
            "• YOLO Annotation Statistics\n"
            "• Validation Set Extraction\n"
            "• YOLO Model Training\n\n"
            "Built with layered architecture design, modular development"
        )


def main():
    root = tk.Tk()
    app = YOLOToolsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()