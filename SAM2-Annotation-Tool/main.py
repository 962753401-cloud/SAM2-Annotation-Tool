"""SAM2 Annotation Tool - Main Entry Point"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    """Main entry point"""
    # Create application
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("SAM2 Annotation Tool")
    app.setOrganizationName("SAM2")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()