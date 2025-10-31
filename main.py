import sys
import os
import json
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QLineEdit, QTextEdit, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QMessageBox, QFileDialog, QTreeWidget,
    QTreeWidgetItem, QSplitter, QFormLayout, QSpinBox, QDoubleSpinBox,
    QDialog, QDialogButtonBox, QHeaderView, QAbstractItemView,
    QTextBrowser, QFrame, QSizePolicy, QProgressBar, QScrollBar,
    QSizeGrip, QToolButton, QStyle, QGridLayout
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import requests
from bs4 import BeautifulSoup
import re
import subprocess
import tempfile

class FullScreenImageDialog(QDialog):
    """Dialog for displaying images in full screen"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.setWindowState(Qt.WindowFullScreen)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.image_label)
        
        # Close button
        close_btn = QPushButton("Close (ESC)")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(close_btn)
        
        self.load_image(image_path)
    
    def load_image(self, image_path):
        """Load and display image"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit screen while maintaining aspect ratio
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                scaled_pixmap = pixmap.scaled(
                    screen_geometry.width() - 100, 
                    screen_geometry.height() - 150,
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Invalid image file")
        else:
            self.image_label.setText("Image file not found")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

class MedicalPrescriptionSystemPyQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Prescription System - PyQt5")
        self.setGeometry(100, 50, 1400, 900)
        
        # Enable window controls including maximize button
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        # Initialize databases and data
        self.setup_databases()
        self.load_doctor_info()
        self.load_drug_database()
        self.load_investigation_database()
        self.load_advice_database()
        
        # Current data
        self.current_patient = None
        self.current_prescription = None
        self.patient_images = []
        self.editing_patient_id = None  # Track which patient is being edited
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data after UI is created
        self.refresh_patient_list()
        
    def setup_databases(self):
        """Initialize SQLite databases"""
        self.conn = sqlite3.connect('medical_prescription.db')
        self.cursor = self.conn.cursor()
        
        # Doctor information table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                degrees TEXT,
                designation TEXT,
                institution TEXT,
                bmdc_reg_no TEXT,
                phone TEXT,
                email TEXT,
                address TEXT
            )
        ''')
        
        # Patients table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                reg_no INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                weight REAL,
                phone TEXT,
                address TEXT,
                created_date TEXT
            )
        ''')
        
        # Prescriptions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_reg_no INTEGER,
                date TEXT,
                cc TEXT,
                diagnosis TEXT,
                vitals TEXT,
                systemic_exam TEXT,
                investigations TEXT,
                drugs TEXT,
                advice TEXT,
                follow_up TEXT,
                doctor_info TEXT,
                FOREIGN KEY (patient_reg_no) REFERENCES patients (reg_no)
            )
        ''')
        
        # Patient images table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_reg_no INTEGER,
                image_path TEXT,
                description TEXT,
                date TEXT,
                FOREIGN KEY (patient_reg_no) REFERENCES patients (reg_no)
            )
        ''')
        
        self.conn.commit()
        
    def load_doctor_info(self):
        """Load doctor information"""
        self.cursor.execute("SELECT * FROM doctors LIMIT 1")
        result = self.cursor.fetchone()
        
        if result:
            self.doctor_info = {
                'name': result[1],
                'degrees': result[2],
                'designation': result[3],
                'institution': result[4],
                'bmdc_reg_no': result[5],
                'phone': result[6],
                'email': result[7],
                'address': result[8]
            }
        else:
            self.doctor_info = {
                'name': "Dr. Your Name",
                'degrees': "MBBS, FCPS",
                'designation': "Assistant Professor",
                'institution': "Dhaka Medical College Hospital",
                'bmdc_reg_no': "A-12345",
                'phone': "01XXXXXXXXX",
                'email': "doctor@email.com",
                'address': "Dhaka, Bangladesh"
            }
    
    def load_drug_database(self):
        """Load drug database"""
        self.drugs_db = []
        
        # Sample drug database with formulation
        sample_drugs = [
            {"trade_name": "Napa", "generic_name": "Paracetamol", "strength": "500mg", "form": "Tablet", "formulation": "Tab. Napa 500mg"},
            {"trade_name": "Ace", "generic_name": "Paracetamol", "strength": "500mg", "form": "Tablet", "formulation": "Tab. Ace 500mg"},
            {"trade_name": "Maxpro", "generic_name": "Esomeprazole", "strength": "40mg", "form": "Capsule", "formulation": "Cap. Maxpro 40mg"},
            {"trade_name": "Rex", "generic_name": "Omeprazole", "strength": "20mg", "form": "Capsule", "formulation": "Cap. Rex 20mg"},
            {"trade_name": "Amodis", "generic_name": "Metronidazole", "strength": "400mg", "form": "Tablet", "formulation": "Tab. Amodis 400mg"},
            {"trade_name": "Ceevit", "generic_name": "Vitamin C", "strength": "500mg", "form": "Tablet", "formulation": "Tab. Ceevit 500mg"},
            {"trade_name": "Zimax", "generic_name": "Azithromycin", "strength": "500mg", "form": "Tablet", "formulation": "Tab. Zimax 500mg"},
            {"trade_name": "Amdocal", "generic_name": "Amlodipine", "strength": "5mg", "form": "Tablet", "formulation": "Tab. Amdocal 5mg"},
            {"trade_name": "Zyloric", "generic_name": "Allopurinol", "strength": "100mg", "form": "Tablet", "formulation": "Tab. Zyloric 100mg"},
            {"trade_name": "Fexo", "generic_name": "Fexofenadine", "strength": "120mg", "form": "Tablet", "formulation": "Tab. Fexo 120mg"},
            {"trade_name": "Montene", "generic_name": "Montelukast", "strength": "10mg", "form": "Tablet", "formulation": "Tab. Montene 10mg"},
            {"trade_name": "Inflagic", "generic_name": "Diclofenac", "strength": "50mg", "form": "Tablet", "formulation": "Tab. Inflagic 50mg"},
            {"trade_name": "Orsaline", "generic_name": "ORS", "strength": "Powder", "form": "Sachet", "formulation": "Sachet Orsaline"},
            {"trade_name": "Seclo", "generic_name": "Hyoscine", "strength": "10mg", "form": "Tablet", "formulation": "Tab. Seclo 10mg"},
            {"trade_name": "Pantonix", "generic_name": "Pantoprazole", "strength": "40mg", "form": "Tablet", "formulation": "Tab. Pantonix 40mg"}
        ]
        
        self.drugs_db = sample_drugs
        
        # Try to load from file if exists
        try:
            with open('drug_database.json', 'r', encoding='utf-8') as f:
                self.drugs_db = json.load(f)
        except:
            # If file doesn't exist, create it with sample data
            with open('drug_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.drugs_db, f, ensure_ascii=False, indent=2)
    
    def save_drug_database(self):
        """Save drug database to file"""
        try:
            with open('drug_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.drugs_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving drug database: {e}")
    
    def load_investigation_database(self):
        """Load investigation database"""
        self.investigations_db = []
        
        # Sample investigations
        sample_investigations = [
            "CBC", "ESR", "RBS", "Fasting Blood Sugar", "HbA1c",
            "S. Creatinine", "S. Urea", "S. Electrolytes", "LFT",
            "Lipid Profile", "Thyroid Profile", "Urine R/E",
            "Stool R/E", "CXR", "ECG", "USG of Whole Abdomen",
            "CT Scan", "MRI", "Echo", "Troponin I", "CRP",
            "Dengue NS1", "Dengue IgG/IgM", "Malaria Antigen",
            "Widal Test", "Blood Culture", "Sputum for AFB"
        ]
        
        self.investigations_db = sample_investigations
        
        try:
            with open('investigation_database.json', 'r', encoding='utf-8') as f:
                self.investigations_db = json.load(f)
        except:
            # If file doesn't exist, create it with sample data
            with open('investigation_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.investigations_db, f, ensure_ascii=False, indent=2)
    
    def save_investigation_database(self):
        """Save investigation database to file"""
        try:
            with open('investigation_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.investigations_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving investigation database: {e}")
    
    def load_advice_database(self):
        """Load Bangla medical advice database"""
        self.advice_db = [
            "পর্যাপ্ত পানি পান করুন",
            "পর্যাপ্ত বিশ্রাম নিন",
            "সময়মতো ওষুধ সেবন করুন",
            "নিয়মিত হাঁটাচলা করুন",
            "পরিচ্ছন্ন থাকুন",
            "পর্যাপ্ত তরল খাবার গ্রহণ করুন",
            "প্যারাসিটামল নির্দেশিত মাত্রায় সেবন করুন",
            "ঠাণ্ডা পানি দিয়ে গা মুছে দিন",
            "হালকা গরম পানি দিয়ে গোসল করুন",
            "চিনি ও মিষ্টি জাতীয় খাবার এড়িয়ে চলুন",
            "নিয়মিত ব্যায়াম করুন",
            "ওজন নিয়ন্ত্রণে রাখুন",
            "রক্তের শর্করা নিয়মিত পরীক্ষা করুন",
            "লবণ কম খান",
            "নিয়মিত রক্তচাপ পরীক্ষা করুন",
            "চর্বি জাতীয় খাবার কম খান",
            "মানসিক চাপ কম রাখুন",
            "ওআরএস খেতে থাকুন",
            "হালকা খাবার যেমন- ভাত, মুড়ি, ডাবের পানি খান",
            "তৈলাক্ত ও মসলাযুক্ত খাবার এড়িয়ে চলুন",
            "ধূলাবালি এড়িয়ে চলুন",
            "ধূমপান পরিহার করুন",
            "গরম পানির ভাপ নিন",
            "মাস্ক ব্যবহার করুন"
        ]
        
        try:
            with open('advice_database.json', 'r', encoding='utf-8') as f:
                self.advice_db = json.load(f)
        except:
            # If file doesn't exist, create it with sample data
            with open('advice_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.advice_db, f, ensure_ascii=False, indent=2)
    
    def save_advice_database(self):
        """Save advice database to file"""
        try:
            with open('advice_database.json', 'w', encoding='utf-8') as f:
                json.dump(self.advice_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving advice database: {e}")

    def setup_ui(self):
        """Setup the main user interface with proper scrollbars"""
        # Create central widget with proper scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for the entire window with both scrollbars
        self.main_scroll_area = QScrollArea()
        self.main_scroll_area.setWidgetResizable(True)
        self.main_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.main_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create scroll content widget
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with doctor info
        self.create_header(self.scroll_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.scroll_layout.addWidget(separator)
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumSize(1200, 600)
        self.scroll_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_doctor_tab()
        self.create_patient_tab()
        self.create_prescription_tab()
        self.create_history_tab()
        self.create_images_tab()
        self.create_drug_database_tab()  # New tab for drug database
        
        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-top: 1px solid #ccc;")
        self.scroll_layout.addWidget(self.status_bar)
        
        # Set the scroll content
        self.main_scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.main_scroll_area)
        
    def create_header(self, layout):
        """Create header with doctor information"""
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #e8f4f8; padding: 10px; border: 1px solid #ccc;")
        header_layout = QVBoxLayout(header_widget)
        
        # Doctor info
        doc_info = self.doctor_info
        info_text = f"Dr. {doc_info['name']} | {doc_info['degrees']} | {doc_info['designation']} | {doc_info['institution']} | BMDC: {doc_info['bmdc_reg_no']} | {doc_info['phone']}"
        
        info_label = QLabel(info_text)
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(info_label)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        new_patient_btn = QPushButton("New Patient")
        prescription_btn = QPushButton("Prescription")
        history_btn = QPushButton("History")
        doctor_info_btn = QPushButton("Doctor Info")
        
        new_patient_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        prescription_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        history_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        doctor_info_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        
        actions_layout.addWidget(new_patient_btn)
        actions_layout.addWidget(prescription_btn)
        actions_layout.addWidget(history_btn)
        actions_layout.addWidget(doctor_info_btn)
        actions_layout.addStretch()
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_widget)
    
    def create_doctor_tab(self):
        """Create doctor information tab with scrollbars"""
        doctor_tab = QWidget()
        layout = QVBoxLayout(doctor_tab)
        
        # Scroll area for doctor tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.doctor_entries = {}
        
        # Create form fields
        fields = [
            ("Name", "name", QLineEdit()),
            ("Degrees & Qualifications", "degrees", QLineEdit()),
            ("Designation", "designation", QLineEdit()),
            ("Institution", "institution", QLineEdit()),
            ("BMDC Registration No", "bmdc_reg_no", QLineEdit()),
            ("Phone Number", "phone", QLineEdit()),
            ("Email", "email", QLineEdit()),
        ]
        
        for label, key, widget in fields:
            widget.setText(self.doctor_info.get(key, ''))
            form_layout.addRow(label, widget)
            self.doctor_entries[key] = widget
        
        # Address field
        self.doctor_address = QTextEdit()
        self.doctor_address.setPlainText(self.doctor_info.get('address', ''))
        self.doctor_address.setMaximumHeight(80)
        form_layout.addRow("Address", self.doctor_address)
        self.doctor_entries['address'] = self.doctor_address
        
        scroll_layout.addLayout(form_layout)
        
        # Save button
        save_btn = QPushButton("Save Doctor Information")
        save_btn.clicked.connect(self.save_doctor_info)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        scroll_layout.addWidget(save_btn)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(doctor_tab, "Doctor Info")
    
    def create_patient_tab(self):
        """Create patient registration and search tab with scrollbars"""
        patient_tab = QWidget()
        layout = QVBoxLayout(patient_tab)
        
        # Scroll area for patient tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Enter name, phone, or registration number...")
        search_layout.addWidget(self.search_entry)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_patient)
        search_layout.addWidget(search_btn)
        
        clear_search_btn = QPushButton("Clear")
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        
        search_layout.addStretch()
        scroll_layout.addLayout(search_layout)
        
        # Patient list table
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(6)
        self.patient_table.setHorizontalHeaderLabels(["Reg No", "Name", "Age", "Gender", "Phone", "Address"])
        self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.patient_table.doubleClicked.connect(self.select_patient)
        self.patient_table.clicked.connect(self.on_patient_table_click)
        scroll_layout.addWidget(self.patient_table)
        
        # Action buttons for patient list
        patient_actions_layout = QHBoxLayout()
        edit_patient_btn = QPushButton("Edit Selected Patient")
        edit_patient_btn.clicked.connect(self.edit_selected_patient)
        delete_patient_btn = QPushButton("Delete Selected Patient")
        delete_patient_btn.clicked.connect(self.delete_selected_patient)
        delete_patient_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        patient_actions_layout.addWidget(edit_patient_btn)
        patient_actions_layout.addWidget(delete_patient_btn)
        patient_actions_layout.addStretch()
        scroll_layout.addLayout(patient_actions_layout)
        
        # Registration form
        form_group = QGroupBox("Patient Registration / Edit")
        form_layout = QGridLayout(form_group)
        
        self.patient_entries = {}
        
        # Form fields in two columns - Ensure English numbers
        fields_left = [
            ("Name:", "name", QLineEdit(), 0, 0),
            ("Age:", "age", QSpinBox(), 1, 0),
            ("Gender:", "gender", QComboBox(), 2, 0),
        ]
        
        fields_right = [
            ("Weight (kg):", "weight", QDoubleSpinBox(), 0, 2),
            ("Phone:", "phone", QLineEdit(), 1, 2),
        ]
        
        # Left column fields
        for label, key, widget, row, col in fields_left:
            form_layout.addWidget(QLabel(label), row, col)
            form_layout.addWidget(widget, row, col + 1)
            
            if isinstance(widget, QSpinBox):
                widget.setRange(0, 150)
                widget.setValue(0)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setRange(0, 300)
                widget.setDecimals(1)
                widget.setValue(0.0)
            elif isinstance(widget, QComboBox):
                widget.addItems(["Male", "Female", "Other"])
            
            self.patient_entries[key] = widget
        
        # Right column fields
        for label, key, widget, row, col in fields_right:
            form_layout.addWidget(QLabel(label), row, col)
            form_layout.addWidget(widget, row, col + 1)
            
            if isinstance(widget, QSpinBox):
                widget.setRange(0, 150)
                widget.setValue(0)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setRange(0, 300)
                widget.setDecimals(1)
                widget.setValue(0.0)
            
            self.patient_entries[key] = widget
        
        # Address field (full width)
        form_layout.addWidget(QLabel("Address:"), 3, 0)
        self.patient_address = QTextEdit()
        self.patient_address.setMaximumHeight(60)
        form_layout.addWidget(self.patient_address, 3, 1, 1, 3)
        self.patient_entries['address'] = self.patient_address
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_patient_btn = QPushButton("Save Patient")
        self.save_patient_btn.clicked.connect(self.save_patient)
        
        self.update_patient_btn = QPushButton("Update Patient")
        self.update_patient_btn.clicked.connect(self.update_patient)
        self.update_patient_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.update_patient_btn.setVisible(False)
        
        self.cancel_edit_btn = QPushButton("Cancel Edit")
        self.cancel_edit_btn.clicked.connect(self.cancel_edit)
        self.cancel_edit_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; }")
        self.cancel_edit_btn.setVisible(False)
        
        clear_patient_btn = QPushButton("Clear Form")
        clear_patient_btn.clicked.connect(self.clear_patient_form)
        
        button_layout.addWidget(self.save_patient_btn)
        button_layout.addWidget(self.update_patient_btn)
        button_layout.addWidget(self.cancel_edit_btn)
        button_layout.addWidget(clear_patient_btn)
        button_layout.addStretch()
        
        form_layout.addLayout(button_layout, 4, 0, 1, 4)
        scroll_layout.addWidget(form_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(patient_tab, "Patients")
    
    def on_patient_table_click(self, index):
        """Handle patient table click to enable edit button"""
        # This method can be used to track selection changes if needed
        pass
    
    def edit_selected_patient(self):
        """Edit the selected patient from the table"""
        selected_items = self.patient_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a patient to edit!")
            return
        
        # Get the registration number from the first column of selected row
        row = selected_items[0].row()
        reg_no = self.patient_table.item(row, 0).text()
        
        self.load_patient_for_editing(reg_no)
    
    def load_patient_for_editing(self, reg_no):
        """Load patient data into form for editing"""
        try:
            self.cursor.execute("SELECT * FROM patients WHERE reg_no=?", (reg_no,))
            patient = self.cursor.fetchone()
            
            if patient:
                # Store the patient ID being edited
                self.editing_patient_id = reg_no
                
                # Fill form with patient data
                self.patient_entries['name'].setText(patient[1])
                self.patient_entries['age'].setValue(patient[2])
                
                # Set gender
                gender_index = self.patient_entries['gender'].findText(patient[3])
                if gender_index >= 0:
                    self.patient_entries['gender'].setCurrentIndex(gender_index)
                
                self.patient_entries['weight'].setValue(patient[4])
                self.patient_entries['phone'].setText(patient[5])
                self.patient_entries['address'].setPlainText(patient[6])
                
                # Switch to edit mode
                self.set_edit_mode(True)
                
                # Show success message
                self.status_bar.setText(f"Editing patient: {patient[1]} (Reg: {reg_no})")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load patient data: {str(e)}")
    
    def set_edit_mode(self, edit_mode):
        """Switch between add and edit modes"""
        if edit_mode:
            self.save_patient_btn.setVisible(False)
            self.update_patient_btn.setVisible(True)
            self.cancel_edit_btn.setVisible(True)
            form_group = self.patient_entries['name'].parent().parent().parent()
            if isinstance(form_group, QGroupBox):
                form_group.setTitle("Edit Patient")
        else:
            self.save_patient_btn.setVisible(True)
            self.update_patient_btn.setVisible(False)
            self.cancel_edit_btn.setVisible(False)
            self.editing_patient_id = None
            form_group = self.patient_entries['name'].parent().parent().parent()
            if isinstance(form_group, QGroupBox):
                form_group.setTitle("Patient Registration")
    
    def update_patient(self):
        """Update existing patient information"""
        if not self.editing_patient_id:
            QMessageBox.warning(self, "Warning", "No patient selected for editing!")
            return
        
        try:
            patient_data = {}
            for key, entry in self.patient_entries.items():
                if isinstance(entry, QTextEdit):
                    patient_data[key] = entry.toPlainText().strip()
                elif isinstance(entry, QSpinBox):
                    patient_data[key] = entry.value()
                elif isinstance(entry, QDoubleSpinBox):
                    patient_data[key] = entry.value()
                elif isinstance(entry, QComboBox):
                    patient_data[key] = entry.currentText()
                else:
                    patient_data[key] = entry.text().strip()
            
            if not patient_data['name']:
                QMessageBox.warning(self, "Warning", "Patient name is required!")
                return
            
            # Update patient in database
            self.cursor.execute('''
                UPDATE patients 
                SET name=?, age=?, gender=?, weight=?, phone=?, address=?
                WHERE reg_no=?
            ''', (
                patient_data['name'], patient_data['age'], patient_data['gender'],
                patient_data['weight'], patient_data['phone'], patient_data['address'],
                self.editing_patient_id
            ))
            
            self.conn.commit()
            self.refresh_patient_list()
            self.clear_patient_form()
            self.set_edit_mode(False)
            
            QMessageBox.information(self, "Success", "Patient information updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update patient: {str(e)}")
    
    def cancel_edit(self):
        """Cancel editing and return to add mode"""
        self.clear_patient_form()
        self.set_edit_mode(False)
        self.status_bar.setText("Edit cancelled")
    
    def delete_selected_patient(self):
        """Delete the selected patient after confirmation"""
        selected_items = self.patient_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a patient to delete!")
            return
        
        # Get patient info for confirmation
        row = selected_items[0].row()
        reg_no = self.patient_table.item(row, 0).text()
        name = self.patient_table.item(row, 1).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete patient:\n\n{name} (Reg: {reg_no})?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete patient from database
                self.cursor.execute("DELETE FROM patients WHERE reg_no=?", (reg_no,))
                self.conn.commit()
                
                # Refresh patient list
                self.refresh_patient_list()
                QMessageBox.information(self, "Success", "Patient deleted successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete patient: {str(e)}")
    
    def create_prescription_tab(self):
        """Create prescription tab with two-column layout and proper scrollbars"""
        prescription_tab = QWidget()
        layout = QVBoxLayout(prescription_tab)
        
        # Patient info display
        self.patient_info_display = QLabel("No patient selected. Please select a patient from the Patients tab.")
        self.patient_info_display.setStyleSheet("background-color: #fff3cd; padding: 10px; border: 1px solid #ffeaa7; font-weight: bold;")
        self.patient_info_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.patient_info_display)
        
        # Scroll area for prescription form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Main content area with two columns
        main_content = QHBoxLayout()
        
        # Left column
        left_column = QVBoxLayout()
        
        # Chief Complaints
        cc_group = QGroupBox("Chief Complaints (CC)")
        cc_layout = QVBoxLayout(cc_group)
        self.cc_entry = QTextEdit()
        self.cc_entry.setMaximumHeight(80)
        cc_layout.addWidget(self.cc_entry)
        left_column.addWidget(cc_group)
        
        # Vitals - Detailed with specific fields
        vitals_group = QGroupBox("Vitals")
        vitals_layout = QGridLayout(vitals_group)
        
        vitals_layout.addWidget(QLabel("BP (mmHg):"), 0, 0)
        self.bp_entry = QLineEdit()
        self.bp_entry.setPlaceholderText("120/80")
        vitals_layout.addWidget(self.bp_entry, 0, 1)
        
        vitals_layout.addWidget(QLabel("Pulse (/min):"), 1, 0)
        self.pulse_entry = QLineEdit()
        self.pulse_entry.setPlaceholderText("72")
        vitals_layout.addWidget(self.pulse_entry, 1, 1)
        
        vitals_layout.addWidget(QLabel("Temperature (°F):"), 2, 0)
        self.temp_entry = QLineEdit()
        self.temp_entry.setPlaceholderText("98.6")
        vitals_layout.addWidget(self.temp_entry, 2, 1)
        
        vitals_layout.addWidget(QLabel("Respiratory Rate (/min):"), 3, 0)
        self.resp_entry = QLineEdit()
        self.resp_entry.setPlaceholderText("16")
        vitals_layout.addWidget(self.resp_entry, 3, 1)
        
        vitals_layout.addWidget(QLabel("SpO2 (%):"), 0, 2)
        self.spo2_entry = QLineEdit()
        self.spo2_entry.setPlaceholderText("98")
        vitals_layout.addWidget(self.spo2_entry, 0, 3)
        
        vitals_layout.addWidget(QLabel("Weight (kg):"), 1, 2)
        self.weight_entry = QLineEdit()
        self.weight_entry.setPlaceholderText("65")
        vitals_layout.addWidget(self.weight_entry, 1, 3)
        
        left_column.addWidget(vitals_group)
        
        # Systemic Examination (Changed from On Examination)
        systemic_group = QGroupBox("Systemic Examination")
        systemic_layout = QVBoxLayout(systemic_group)
        self.systemic_entry = QTextEdit()
        self.systemic_entry.setMaximumHeight(100)
        systemic_layout.addWidget(self.systemic_entry)
        left_column.addWidget(systemic_group)
        
        # Diagnosis
        diagnosis_group = QGroupBox("Diagnosis")
        diagnosis_layout = QVBoxLayout(diagnosis_group)
        self.diagnosis_entry = QTextEdit()
        self.diagnosis_entry.setMaximumHeight(80)
        diagnosis_layout.addWidget(self.diagnosis_entry)
        left_column.addWidget(diagnosis_group)
        
        # Right column
        right_column = QVBoxLayout()
        
        # Investigations with list selection and custom add
        investigations_group = QGroupBox("Investigations")
        investigations_layout = QVBoxLayout(investigations_group)
        
        # Investigation selection
        investigation_selection_layout = QHBoxLayout()
        
        self.investigation_list = QListWidget()
        self.investigation_list.addItems(self.investigations_db)
        self.investigation_list.setMaximumHeight(100)
        
        investigation_buttons_layout = QVBoxLayout()
        add_investigation_btn = QPushButton("Add Selected")
        add_investigation_btn.clicked.connect(self.add_selected_investigation)
        
        self.investigation_search = QLineEdit()
        self.investigation_search.setPlaceholderText("Add custom investigation...")
        
        add_custom_investigation_btn = QPushButton("Add Custom")
        add_custom_investigation_btn.clicked.connect(self.add_custom_investigation)
        
        investigation_buttons_layout.addWidget(add_investigation_btn)
        investigation_buttons_layout.addWidget(self.investigation_search)
        investigation_buttons_layout.addWidget(add_custom_investigation_btn)
        investigation_buttons_layout.addStretch()
        
        investigation_selection_layout.addWidget(self.investigation_list)
        investigation_selection_layout.addLayout(investigation_buttons_layout)
        
        # Selected investigations
        self.selected_investigations = QTextEdit()
        self.selected_investigations.setMaximumHeight(120)
        self.selected_investigations.setPlaceholderText("Selected investigations will appear here...")
        
        investigations_layout.addLayout(investigation_selection_layout)
        investigations_layout.addWidget(QLabel("Selected Investigations:"))
        investigations_layout.addWidget(self.selected_investigations)
        right_column.addWidget(investigations_group)
        
        # Drugs section
        drugs_group = QGroupBox("Drugs/Prescription")
        drugs_layout = QVBoxLayout(drugs_group)
        
        # Drug selection
        drug_selection_layout = QHBoxLayout()
        
        self.drug_search = QLineEdit()
        self.drug_search.setPlaceholderText("Search drug...")
        self.drug_search.textChanged.connect(self.filter_drugs)
        
        self.drug_combo = QComboBox()
        self.drug_combo.addItems([drug['formulation'] for drug in self.drugs_db])
        
        add_custom_drug_btn = QPushButton("Add Custom")
        add_custom_drug_btn.clicked.connect(self.add_custom_drug)
        
        drug_selection_layout.addWidget(QLabel("Drug:"))
        drug_selection_layout.addWidget(self.drug_search)
        drug_selection_layout.addWidget(self.drug_combo)
        drug_selection_layout.addWidget(add_custom_drug_btn)
        
        # Drug details in grid
        drug_details_layout = QGridLayout()
        
        drug_details_layout.addWidget(QLabel("Dose/Frequency:"), 0, 0)
        
        # ComboBox for common dose frequencies with custom entry option - NOW WITH BENGALI
        dose_frequency_layout = QHBoxLayout()
        self.dosage_combo = QComboBox()
        self.dosage_combo.setEditable(True)  # Allow custom entry
        # English frequencies
        self.dosage_combo.addItems([
            "0+0+1", "0+1+0", "1+0+0", "0+1+1", 
            "1+0+1", "1+1+0", "1+1+1", "1+0+0+1",
            "1+1+1+1", "0+0+0+1", "SOS", "When required"
        ])
        # Bengali frequencies
        self.dosage_combo.addItems([
            "০+০+১", "০+১+০", "১+০+০", "০+১+১", 
            "১+০+১", "১+১+০", "১+১+১", "১+০+০+১",
            "১+১+১+১", "০+০+০+১", "প্রয়োজনমত", "খাওয়ার পর"
        ])
        self.dosage_combo.setCurrentText("1+1+1")  # Default value
        dose_frequency_layout.addWidget(self.dosage_combo)
        
        drug_details_layout.addLayout(dose_frequency_layout, 0, 1)
        
        drug_details_layout.addWidget(QLabel("Duration:"), 1, 0)
        
        # ComboBox for duration with days and months - NOW WITH BENGALI
        duration_layout = QHBoxLayout()
        self.duration_combo = QComboBox()
        self.duration_combo.setEditable(True)  # Allow custom entry
        # English durations - days
        for i in range(1, 15):
            self.duration_combo.addItem(f"{i} day{'s' if i > 1 else ''}")
        # English durations - months
        for i in range(1, 7):
            self.duration_combo.addItem(f"{i} month{'s' if i > 1 else ''}")
        # Bengali durations - days
        bengali_numbers = ["১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯", "১০", "১১", "১২", "১৩", "১৪"]
        for i, num in enumerate(bengali_numbers, 1):
            self.duration_combo.addItem(f"{num} দিন")
        # Bengali durations - months
        bengali_months = ["১", "২", "৩", "৪", "৫", "৬"]
        for i, num in enumerate(bengali_months, 1):
            self.duration_combo.addItem(f"{num} মাস")
        
        self.duration_combo.setCurrentText("7 days")  # Default value
        duration_layout.addWidget(self.duration_combo)
        
        drug_details_layout.addLayout(duration_layout, 1, 1)
        
        drug_details_layout.addWidget(QLabel("Instructions:"), 2, 0)
        
        # ComboBox for instructions with English and Bangla options
        instructions_layout = QHBoxLayout()
        self.instructions_combo = QComboBox()
        self.instructions_combo.setEditable(True)  # Allow custom entry
        self.instructions_combo.addItems([
            "Before meal", 
            "After meal", 
            "খাবার আগে", 
            "খাবার পরে"
        ])
        self.instructions_combo.setCurrentText("After meal")  # Default value
        instructions_layout.addWidget(self.instructions_combo)
        
        drug_details_layout.addLayout(instructions_layout, 2, 1)
        
        add_drug_btn = QPushButton("Add Drug")
        add_drug_btn.clicked.connect(self.add_drug_to_prescription)
        drug_details_layout.addWidget(add_drug_btn, 3, 0, 1, 2)
        
        # Drugs table
        self.drugs_table = QTableWidget()
        self.drugs_table.setColumnCount(4)
        self.drugs_table.setHorizontalHeaderLabels(["Formulation", "Dose/Frequency", "Duration", "Instructions"])
        self.drugs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        drugs_layout.addLayout(drug_selection_layout)
        drugs_layout.addLayout(drug_details_layout)
        drugs_layout.addWidget(self.drugs_table)
        right_column.addWidget(drugs_group)
        
        # Advice with list selection and custom add
        advice_group = QGroupBox("Advice")
        advice_layout = QVBoxLayout(advice_group)
        
        # Advice selection
        advice_selection_layout = QHBoxLayout()
        
        self.advice_list = QListWidget()
        self.advice_list.addItems(self.advice_db)
        self.advice_list.setMaximumHeight(100)
        
        advice_buttons_layout = QVBoxLayout()
        add_advice_btn = QPushButton("Add Selected")
        add_advice_btn.clicked.connect(self.add_selected_advice)
        
        self.advice_search = QLineEdit()
        self.advice_search.setPlaceholderText("Add custom advice...")
        
        add_custom_advice_btn = QPushButton("Add Custom")
        add_custom_advice_btn.clicked.connect(self.add_custom_advice)
        
        advice_buttons_layout.addWidget(add_advice_btn)
        advice_buttons_layout.addWidget(self.advice_search)
        advice_buttons_layout.addWidget(add_custom_advice_btn)
        advice_buttons_layout.addStretch()
        
        advice_selection_layout.addWidget(self.advice_list)
        advice_selection_layout.addLayout(advice_buttons_layout)
        
        # Selected advice
        self.advice_entry = QTextEdit()
        self.advice_entry.setMaximumHeight(120)
        self.advice_entry.setPlaceholderText("Medical advice will appear here...")
        
        advice_layout.addLayout(advice_selection_layout)
        advice_layout.addWidget(QLabel("Selected Advice:"))
        advice_layout.addWidget(self.advice_entry)
        right_column.addWidget(advice_group)
        
        # Follow up
        follow_up_group = QGroupBox("Follow Up")
        follow_up_layout = QHBoxLayout(follow_up_group)
        self.follow_up_entry = QLineEdit()
        self.follow_up_entry.setPlaceholderText("e.g., After 7 days")
        follow_up_layout.addWidget(QLabel("Follow up after:"))
        follow_up_layout.addWidget(self.follow_up_entry)
        follow_up_layout.addStretch()
        right_column.addWidget(follow_up_group)
        
        # Add columns to main content
        main_content.addLayout(left_column)
        main_content.addLayout(right_column)
        scroll_layout.addLayout(main_content)
        
        # Action buttons
        button_layout = QHBoxLayout()
        save_prescription_btn = QPushButton("Save Prescription")
        generate_pdf_btn = QPushButton("Generate PDF")
        print_prescription_btn = QPushButton("Print Prescription")
        clear_prescription_btn = QPushButton("Clear Form")
        
        save_prescription_btn.clicked.connect(self.save_prescription)
        generate_pdf_btn.clicked.connect(self.generate_pdf)
        print_prescription_btn.clicked.connect(self.print_prescription)
        clear_prescription_btn.clicked.connect(self.clear_prescription_form)
        
        button_layout.addWidget(save_prescription_btn)
        button_layout.addWidget(generate_pdf_btn)
        button_layout.addWidget(print_prescription_btn)
        button_layout.addWidget(clear_prescription_btn)
        button_layout.addStretch()
        
        scroll_layout.addLayout(button_layout)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(prescription_tab, "Prescription")
    
    def create_drug_database_tab(self):
        """Create a tab for adding new drugs to the database"""
        drug_db_tab = QWidget()
        layout = QVBoxLayout(drug_db_tab)
        
        # Scroll area for drug database tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Drug database form
        form_group = QGroupBox("Add New Drug to Database")
        form_layout = QFormLayout(form_group)
        
        # Formulation type dropdown - Added Inhaler and Powder
        self.formulation_combo = QComboBox()
        self.formulation_combo.addItems(["Tab.", "Cap.", "Syr.", "Inj.", "Drop.", "Crm.", "Oint.", "Sachet", "Supp.", "Inhaler", "Powder"])
        form_layout.addRow("Formulation:", self.formulation_combo)
        
        # Trade name
        self.trade_name_entry = QLineEdit()
        self.trade_name_entry.setPlaceholderText("Enter trade name")
        form_layout.addRow("Trade Name:", self.trade_name_entry)
        
        # Strength
        self.strength_entry = QLineEdit()
        self.strength_entry.setPlaceholderText("e.g., 500mg, 10mg/ml")
        form_layout.addRow("Strength:", self.strength_entry)
        
        # Generic name
        self.generic_name_entry = QLineEdit()
        self.generic_name_entry.setPlaceholderText("Enter generic name")
        form_layout.addRow("Generic Name:", self.generic_name_entry)
        
        # Preview of formulation
        self.formulation_preview = QLabel("Formulation preview will appear here")
        self.formulation_preview.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        form_layout.addRow("Formulation Preview:", self.formulation_preview)
        
        # Connect signals to update preview
        self.formulation_combo.currentTextChanged.connect(self.update_formulation_preview)
        self.trade_name_entry.textChanged.connect(self.update_formulation_preview)
        self.strength_entry.textChanged.connect(self.update_formulation_preview)
        
        # Save button
        save_drug_btn = QPushButton("Save Drug to Database")
        save_drug_btn.clicked.connect(self.save_drug_to_database)
        save_drug_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        form_layout.addRow(save_drug_btn)
        
        scroll_layout.addWidget(form_group)
        
        # Current drugs list
        drugs_list_group = QGroupBox("Current Drugs in Database")
        drugs_list_layout = QVBoxLayout(drugs_list_group)
        
        self.drugs_list_widget = QListWidget()
        self.drugs_list_widget.addItems([drug['formulation'] for drug in self.drugs_db])
        drugs_list_layout.addWidget(self.drugs_list_widget)
        
        scroll_layout.addWidget(drugs_list_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(drug_db_tab, "Drug Database")
    
    def update_formulation_preview(self):
        """Update the formulation preview based on form inputs"""
        formulation = self.formulation_combo.currentText()
        trade_name = self.trade_name_entry.text()
        strength = self.strength_entry.text()
        
        if trade_name and strength:
            preview = f"{formulation} {trade_name} {strength}"
        elif trade_name:
            preview = f"{formulation} {trade_name}"
        else:
            preview = "Formulation preview will appear here"
        
        self.formulation_preview.setText(preview)
    
    def save_drug_to_database(self):
        """Save new drug to database"""
        try:
            formulation_type = self.formulation_combo.currentText()
            trade_name = self.trade_name_entry.text().strip()
            strength = self.strength_entry.text().strip()
            generic_name = self.generic_name_entry.text().strip()
            
            if not trade_name:
                QMessageBox.warning(self, "Warning", "Trade name is required!")
                return
            
            if not generic_name:
                QMessageBox.warning(self, "Warning", "Generic name is required!")
                return
            
            # Create formulation
            formulation = f"{formulation_type} {trade_name}"
            if strength:
                formulation += f" {strength}"
            
            # Check if drug already exists
            for drug in self.drugs_db:
                if drug['formulation'].lower() == formulation.lower():
                    QMessageBox.warning(self, "Warning", "This drug already exists in the database!")
                    return
            
            # Create new drug entry
            new_drug = {
                "trade_name": trade_name,
                "generic_name": generic_name,
                "strength": strength,
                "form": formulation_type.replace('.', ''),
                "formulation": formulation
            }
            
            # Add to database
            self.drugs_db.append(new_drug)
            self.save_drug_database()
            
            # Update UI
            self.drugs_list_widget.addItem(formulation)
            self.drug_combo.addItem(formulation)
            
            # Clear form
            self.trade_name_entry.clear()
            self.strength_entry.clear()
            self.generic_name_entry.clear()
            
            QMessageBox.information(self, "Success", "Drug saved to database successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save drug: {str(e)}")
    
    def create_history_tab(self):
        """Create patient history tab with scrollbars"""
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)
        
        # Scroll area for history tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Patient selection
        patient_select_layout = QHBoxLayout()
        patient_select_layout.addWidget(QLabel("Select Patient:"))
        self.history_patient_combo = QComboBox()
        self.history_patient_combo.currentTextChanged.connect(self.load_patient_history)
        patient_select_layout.addWidget(self.history_patient_combo)
        patient_select_layout.addStretch()
        
        scroll_layout.addLayout(patient_select_layout)
        
        # History display
        self.history_display = QTextBrowser()
        self.history_display.setMinimumHeight(400)
        scroll_layout.addWidget(self.history_display)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(history_tab, "History")
    
    def create_images_tab(self):
        """Create patient images tab with enhanced features"""
        images_tab = QWidget()
        layout = QVBoxLayout(images_tab)
        
        # Scroll area for images tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Patient selection
        patient_select_layout = QHBoxLayout()
        patient_select_layout.addWidget(QLabel("Select Patient:"))
        self.images_patient_combo = QComboBox()
        self.images_patient_combo.currentTextChanged.connect(self.load_patient_images)
        patient_select_layout.addWidget(self.images_patient_combo)
        patient_select_layout.addStretch()
        
        scroll_layout.addLayout(patient_select_layout)
        
        # Image upload section
        upload_group = QGroupBox("Upload New Image")
        upload_layout = QVBoxLayout(upload_group)
        
        upload_controls_layout = QHBoxLayout()
        self.upload_image_btn = QPushButton("Select Image")
        self.upload_image_btn.clicked.connect(self.select_image)
        
        self.image_description = QLineEdit()
        self.image_description.setPlaceholderText("Image description...")
        
        upload_controls_layout.addWidget(self.upload_image_btn)
        upload_controls_layout.addWidget(self.image_description)
        upload_controls_layout.addStretch()
        
        upload_layout.addLayout(upload_controls_layout)
        scroll_layout.addWidget(upload_group)
        
        # Images display section
        images_display_group = QGroupBox("Patient Images")
        images_display_layout = QVBoxLayout(images_display_group)
        
        self.images_display = QWidget()
        self.images_layout = QVBoxLayout(self.images_display)
        images_display_layout.addWidget(self.images_display)
        
        scroll_layout.addWidget(images_display_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(images_tab, "Images")

    def load_patient_images(self):
        """Load patient images with edit/delete options and full-screen viewing"""
        try:
            # Clear current images
            for i in reversed(range(self.images_layout.count())): 
                widget = self.images_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            patient_id = self.images_patient_combo.currentData()
            if not patient_id:
                no_patient_label = QLabel("Please select a patient to view images.")
                no_patient_label.setAlignment(Qt.AlignCenter)
                self.images_layout.addWidget(no_patient_label)
                return
            
            self.cursor.execute('''
                SELECT * FROM patient_images 
                WHERE patient_reg_no = ? 
                ORDER BY date DESC
            ''', (patient_id,))
            
            images = self.cursor.fetchall()
            
            if not images:
                no_images_label = QLabel("No images found for this patient.")
                no_images_label.setAlignment(Qt.AlignCenter)
                self.images_layout.addWidget(no_images_label)
                return
            
            # Create scroll area for images
            images_scroll = QScrollArea()
            images_scroll.setWidgetResizable(True)
            images_scroll.setMinimumHeight(500)
            
            images_widget = QWidget()
            images_grid = QVBoxLayout(images_widget)
            
            for image in images:
                image_id, patient_reg_no, image_path, description, date = image
                
                # Create image group with border
                image_group = QGroupBox(f"Image - {datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M %p')}")
                image_group.setStyleSheet("QGroupBox { border: 2px solid #cccccc; border-radius: 5px; margin-top: 10px; }")
                image_group_layout = QVBoxLayout(image_group)
                
                # Image display with clickable functionality
                image_display_widget = QWidget()
                image_display_layout = QHBoxLayout(image_display_widget)
                
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # Scale image for display
                        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        image_label = QLabel()
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setStyleSheet("border: 1px solid #aaaaaa; padding: 5px;")
                        image_label.setCursor(Qt.PointingHandCursor)
                        image_label.mousePressEvent = lambda event, path=image_path: self.view_image_fullscreen(path)
                        
                        # Add click message
                        click_label = QLabel("📸 Click image to view full screen")
                        click_label.setStyleSheet("color: #666666; font-size: 10px; font-style: italic;")
                        click_label.setAlignment(Qt.AlignCenter)
                        
                        image_display_layout.addWidget(image_label)
                    else:
                        error_label = QLabel("Invalid image file")
                        image_display_layout.addWidget(error_label)
                else:
                    missing_label = QLabel("Image file not found")
                    image_display_layout.addWidget(missing_label)
                
                image_group_layout.addWidget(image_display_widget)
                
                # Description
                if description:
                    desc_label = QLabel(f"Description: {description}")
                    desc_label.setStyleSheet("font-weight: bold; margin: 5px;")
                    image_group_layout.addWidget(desc_label)
                
                # Action buttons (Edit and Delete)
                button_layout = QHBoxLayout()
                
                # Edit button
                edit_btn = QPushButton("Edit Description")
                edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 5px; }")
                edit_btn.clicked.connect(lambda checked, img_id=image_id, current_desc=description: 
                                       self.edit_image_description(img_id, current_desc))
                
                # Delete button
                delete_btn = QPushButton("Delete Image")
                delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 5px; }")
                delete_btn.clicked.connect(lambda checked, img_id=image_id, img_path=image_path: 
                                         self.delete_patient_image(img_id, img_path))
                
                button_layout.addWidget(edit_btn)
                button_layout.addWidget(delete_btn)
                button_layout.addStretch()
                
                image_group_layout.addLayout(button_layout)
                image_group_layout.addWidget(click_label)  # Add click message below buttons
                
                images_grid.addWidget(image_group)
            
            # Add stretch to push everything to top
            images_grid.addStretch()
            
            images_scroll.setWidget(images_widget)
            self.images_layout.addWidget(images_scroll)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load patient images: {str(e)}")

    def view_image_fullscreen(self, image_path):
        """Open image in full screen dialog"""
        try:
            if os.path.exists(image_path):
                fullscreen_dialog = FullScreenImageDialog(image_path, self)
                fullscreen_dialog.exec_()
            else:
                QMessageBox.warning(self, "Warning", "Image file not found!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open image: {str(e)}")

    def edit_image_description(self, image_id, current_description):
        """Edit image description"""
        try:
            # Create edit dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Image Description")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            # Description input
            layout.addWidget(QLabel("Image Description:"))
            description_edit = QTextEdit()
            description_edit.setPlainText(current_description)
            description_edit.setMaximumHeight(80)
            layout.addWidget(description_edit)
            
            # Buttons
            button_layout = QHBoxLayout()
            save_btn = QPushButton("Save")
            cancel_btn = QPushButton("Cancel")
            
            save_btn.clicked.connect(lambda: self.save_image_description(image_id, description_edit.toPlainText(), dialog))
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit image description: {str(e)}")

    def save_image_description(self, image_id, new_description, dialog):
        """Save updated image description to database"""
        try:
            self.cursor.execute('''
                UPDATE patient_images 
                SET description = ? 
                WHERE id = ?
            ''', (new_description.strip(), image_id))
            
            self.conn.commit()
            dialog.accept()
            
            # Reload images to show updated description
            self.load_patient_images()
            
            QMessageBox.information(self, "Success", "Image description updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update image description: {str(e)}")

    def delete_patient_image(self, image_id, image_path):
        """Delete patient image after confirmation"""
        try:
            # Confirm deletion
            reply = QMessageBox.question(
                self, 
                "Confirm Deletion", 
                "Are you sure you want to delete this image?\n\nThis action cannot be undone!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Delete from database
                self.cursor.execute("DELETE FROM patient_images WHERE id = ?", (image_id,))
                self.conn.commit()
                
                # Delete physical file if it exists
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as file_error:
                    print(f"Warning: Could not delete image file: {file_error}")
                
                # Reload images
                self.load_patient_images()
                
                QMessageBox.information(self, "Success", "Image deleted successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete image: {str(e)}")

    # ==================== DATABASE MANAGEMENT METHODS ====================
    
    def save_doctor_info(self):
        """Save doctor information to database"""
        try:
            doctor_data = {}
            for key, entry in self.doctor_entries.items():
                if isinstance(entry, QTextEdit):
                    doctor_data[key] = entry.toPlainText().strip()
                else:
                    doctor_data[key] = entry.text().strip()
            
            # Check if doctor record exists
            self.cursor.execute("SELECT COUNT(*) FROM doctors")
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record
                self.cursor.execute('''
                    UPDATE doctors SET 
                    name=?, degrees=?, designation=?, institution=?, 
                    bmdc_reg_no=?, phone=?, email=?, address=?
                ''', (
                    doctor_data['name'], doctor_data['degrees'], 
                    doctor_data['designation'], doctor_data['institution'],
                    doctor_data['bmdc_reg_no'], doctor_data['phone'],
                    doctor_data['email'], doctor_data['address']
                ))
            else:
                # Insert new record
                self.cursor.execute('''
                    INSERT INTO doctors (name, degrees, designation, institution, bmdc_reg_no, phone, email, address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doctor_data['name'], doctor_data['degrees'], 
                    doctor_data['designation'], doctor_data['institution'],
                    doctor_data['bmdc_reg_no'], doctor_data['phone'],
                    doctor_data['email'], doctor_data['address']
                ))
            
            self.conn.commit()
            self.load_doctor_info()
            QMessageBox.information(self, "Success", "Doctor information saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save doctor information: {str(e)}")
    
    def refresh_patient_list(self):
        """Refresh patient list in tables and comboboxes"""
        try:
            self.cursor.execute("SELECT reg_no, name, age, gender, phone, address FROM patients ORDER BY reg_no DESC")
            patients = self.cursor.fetchall()
            
            # Update patient table
            self.patient_table.setRowCount(len(patients))
            for row, patient in enumerate(patients):
                for col, value in enumerate(patient):
                    self.patient_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            # Update history patient combo
            self.history_patient_combo.clear()
            self.history_patient_combo.addItem("Select Patient")
            for patient in patients:
                self.history_patient_combo.addItem(f"{patient[0]} - {patient[1]}", patient[0])
            
            # Update images patient combo
            self.images_patient_combo.clear()
            self.images_patient_combo.addItem("Select Patient")
            for patient in patients:
                self.images_patient_combo.addItem(f"{patient[0]} - {patient[1]}", patient[0])
                
        except Exception as e:
            print(f"Error refreshing patient list: {e}")
    
    def search_patient(self):
        """Search patients"""
        search_term = self.search_entry.text().strip()
        if not search_term:
            self.refresh_patient_list()
            return
        
        try:
            self.cursor.execute('''
                SELECT reg_no, name, age, gender, phone, address 
                FROM patients 
                WHERE name LIKE ? OR phone LIKE ? OR reg_no = ?
                ORDER BY reg_no DESC
            ''', (f'%{search_term}%', f'%{search_term}%', search_term))
            
            patients = self.cursor.fetchall()
            self.patient_table.setRowCount(len(patients))
            
            for row, patient in enumerate(patients):
                for col, value in enumerate(patient):
                    self.patient_table.setItem(row, col, QTableWidgetItem(str(value)))
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")
    
    def clear_search(self):
        """Clear search and refresh patient list"""
        self.search_entry.clear()
        self.refresh_patient_list()
    
    def select_patient(self, index):
        """Select patient from table for prescription"""
        row = index.row()
        reg_no = self.patient_table.item(row, 0).text()
        name = self.patient_table.item(row, 1).text()
        age = self.patient_table.item(row, 2).text()
        gender = self.patient_table.item(row, 3).text()
        
        # FIXED: Get weight from database for the selected patient
        try:
            self.cursor.execute("SELECT weight FROM patients WHERE reg_no=?", (reg_no,))
            result = self.cursor.fetchone()
            weight = str(result[0]) if result and result[0] else "0"
        except:
            weight = "0"
        
        self.current_patient = {
            'reg_no': reg_no,
            'name': name,
            'age': age,
            'gender': gender,
            'weight': weight  # FIXED: Store weight in current_patient
        }
        
        # Update patient info display - FIXED: Show actual weight
        self.patient_info_display.setText(f"Patient: {name} (Reg: {reg_no}) | Age: {age} | Gender: {gender} | Weight: {weight}kg")
        
        # Switch to prescription tab
        self.tab_widget.setCurrentIndex(2)
    
    def save_patient(self):
        """Save new patient to database"""
        try:
            patient_data = {}
            for key, entry in self.patient_entries.items():
                if isinstance(entry, QTextEdit):
                    patient_data[key] = entry.toPlainText().strip()
                elif isinstance(entry, QSpinBox):
                    patient_data[key] = entry.value()
                elif isinstance(entry, QDoubleSpinBox):
                    patient_data[key] = entry.value()
                elif isinstance(entry, QComboBox):
                    patient_data[key] = entry.currentText()
                else:
                    patient_data[key] = entry.text().strip()
            
            if not patient_data['name']:
                QMessageBox.warning(self, "Warning", "Patient name is required!")
                return
            
            # Insert patient
            self.cursor.execute('''
                INSERT INTO patients (name, age, gender, weight, phone, address, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_data['name'], patient_data['age'], patient_data['gender'],
                patient_data['weight'], patient_data['phone'], patient_data['address'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            self.conn.commit()
            self.refresh_patient_list()
            self.clear_patient_form()
            QMessageBox.information(self, "Success", "Patient saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save patient: {str(e)}")
    
    def clear_patient_form(self):
        """Clear patient registration form"""
        for key, entry in self.patient_entries.items():
            if isinstance(entry, QTextEdit):
                entry.clear()
            elif isinstance(entry, QSpinBox):
                entry.setValue(0)
            elif isinstance(entry, QDoubleSpinBox):
                entry.setValue(0.0)
            elif isinstance(entry, QComboBox):
                entry.setCurrentIndex(0)
            else:
                entry.clear()
    
    # ==================== DRUG AND DATABASE METHODS ====================
    
    def filter_drugs(self):
        """Filter drugs based on search text"""
        search_text = self.drug_search.text().lower()
        self.drug_combo.clear()
        
        filtered_drugs = []
        for drug in self.drugs_db:
            if (search_text in drug['formulation'].lower() or 
                search_text in drug['generic_name'].lower() or
                search_text in drug['trade_name'].lower()):
                filtered_drugs.append(drug['formulation'])
        
        self.drug_combo.addItems(filtered_drugs)
    
    def add_selected_investigation(self):
        """Add selected investigation from list"""
        selected_items = self.investigation_list.selectedItems()
        for item in selected_items:
            investigation = item.text()
            current_text = self.selected_investigations.toPlainText()
            if current_text:
                new_text = current_text + "\n" + investigation
            else:
                new_text = investigation
            self.selected_investigations.setPlainText(new_text)
    
    def add_selected_advice(self):
        """Add selected advice from list"""
        selected_items = self.advice_list.selectedItems()
        for item in selected_items:
            advice = item.text()
            current_text = self.advice_entry.toPlainText()
            if current_text:
                new_text = current_text + "\n" + advice
            else:
                new_text = advice
            self.advice_entry.setPlainText(new_text)
    
    def add_custom_investigation(self):
        """Add custom investigation to database"""
        investigation = self.investigation_search.text().strip()
        if investigation:
            # Add to current text
            current_text = self.selected_investigations.toPlainText()
            if current_text:
                new_text = current_text + "\n" + investigation
            else:
                new_text = investigation
            self.selected_investigations.setPlainText(new_text)
            
            # Add to database if not exists
            if investigation not in self.investigations_db:
                self.investigations_db.append(investigation)
                self.investigation_list.addItem(investigation)
                self.save_investigation_database()
            
            self.investigation_search.clear()
    
    def add_custom_drug(self):
        """Add custom drug to database"""
        drug_name = self.drug_search.text().strip()
        if drug_name:
            # Create a new drug entry with formulation format
            # Try to detect form and create formulation
            form = "Tab."
            if any(word in drug_name.lower() for word in ['cap', 'capsule']):
                form = "Cap."
            elif any(word in drug_name.lower() for word in ['syr', 'syrup']):
                form = "Syr."
            elif any(word in drug_name.lower() for word in ['inj', 'injection']):
                form = "Inj."
            elif any(word in drug_name.lower() for word in ['drop', 'drops']):
                form = "Drop."
            elif any(word in drug_name.lower() for word in ['cream', 'ointment']):
                form = "Crm."
            elif any(word in drug_name.lower() for word in ['inhaler']):
                form = "Inhaler"
            elif any(word in drug_name.lower() for word in ['powder']):
                form = "Powder"
            
            # Create formulation
            formulation = f"{form} {drug_name}"
            
            # Add to database if not exists
            drug_exists = False
            for drug in self.drugs_db:
                if drug['formulation'].lower() == formulation.lower():
                    drug_exists = True
                    break
            
            if not drug_exists:
                new_drug = {
                    "trade_name": drug_name,
                    "generic_name": drug_name,
                    "strength": "",
                    "form": form.replace('.', ''),
                    "formulation": formulation
                }
                self.drugs_db.append(new_drug)
                self.drug_combo.addItem(formulation)
                self.save_drug_database()
            
            # Set as current selection
            self.drug_combo.setCurrentText(formulation)
            self.drug_search.clear()
    
    def add_custom_advice(self):
        """Add custom advice to database"""
        advice = self.advice_search.text().strip()
        if advice:
            # Add to current text
            current_text = self.advice_entry.toPlainText()
            if current_text:
                new_text = current_text + "\n" + advice
            else:
                new_text = advice
            self.advice_entry.setPlainText(new_text)
            
            # Add to database if not exists
            if advice not in self.advice_db:
                self.advice_db.append(advice)
                self.advice_list.addItem(advice)
                self.save_advice_database()
            
            self.advice_search.clear()
    
    def add_drug_to_prescription(self):
        """Add drug to prescription table"""
        try:
            drug_text = self.drug_combo.currentText()
            if not drug_text:
                QMessageBox.warning(self, "Warning", "Please select or enter a drug!")
                return
            
            # Get dosage from combo box (allows custom entry)
            dosage = self.dosage_combo.currentText().strip()
            # Get duration from combo box (allows custom entry)
            duration = self.duration_combo.currentText().strip()
            # Get instructions from combo box (allows custom entry)
            instructions = self.instructions_combo.currentText().strip()
            
            if not dosage:
                QMessageBox.warning(self, "Warning", "Please enter dosage/frequency!")
                return
            
            # Add to table
            row = self.drugs_table.rowCount()
            self.drugs_table.insertRow(row)
            
            self.drugs_table.setItem(row, 0, QTableWidgetItem(drug_text))
            self.drugs_table.setItem(row, 1, QTableWidgetItem(dosage))
            self.drugs_table.setItem(row, 2, QTableWidgetItem(duration))
            self.drugs_table.setItem(row, 3, QTableWidgetItem(instructions))
            
            # Clear drug form (keep default values in combos)
            # The combos will keep their current selections for next drug
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add drug: {str(e)}")
    
    def save_prescription(self):
        """Save prescription to database"""
        if not self.current_patient:
            QMessageBox.warning(self, "Warning", "Please select a patient first!")
            return
        
        try:
            # Collect vitals data - FIXED: Keep vitals with line breaks
            vitals_data = []
            if self.bp_entry.text():
                vitals_data.append(f"• BP: {self.bp_entry.text()} mmHg")
            if self.pulse_entry.text():
                vitals_data.append(f"• Pulse: {self.pulse_entry.text()}/min")
            if self.temp_entry.text():
                vitals_data.append(f"• Temperature: {self.temp_entry.text()}°F")
            if self.resp_entry.text():
                vitals_data.append(f"• Respiratory Rate: {self.resp_entry.text()}/min")
            if self.spo2_entry.text():
                vitals_data.append(f"• SpO2: {self.spo2_entry.text()}%")
            if self.weight_entry.text():
                vitals_data.append(f"• Weight: {self.weight_entry.text()} kg")
            
            # FIXED: Join vitals with line breaks
            vitals_text = "\n".join(vitals_data)
            
            # Collect drugs data
            drugs_data = []
            for row in range(self.drugs_table.rowCount()):
                drug = {
                    'formulation': self.drugs_table.item(row, 0).text(),
                    'dosage': self.drugs_table.item(row, 1).text(),
                    'duration': self.drugs_table.item(row, 2).text(),
                    'instructions': self.drugs_table.item(row, 3).text()
                }
                drugs_data.append(drug)
            
            # Save to database
            self.cursor.execute('''
                INSERT INTO prescriptions 
                (patient_reg_no, date, cc, diagnosis, vitals, systemic_exam, investigations, drugs, advice, follow_up, doctor_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_patient['reg_no'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.cc_entry.toPlainText(),
                self.diagnosis_entry.toPlainText(),
                vitals_text,  # FIXED: Now uses line break separated vitals
                self.systemic_entry.toPlainText(),
                self.selected_investigations.toPlainText(),
                json.dumps(drugs_data),
                self.advice_entry.toPlainText(),
                self.follow_up_entry.text(),
                json.dumps(self.doctor_info)
            ))
            
            self.conn.commit()
            QMessageBox.information(self, "Success", "Prescription saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save prescription: {str(e)}")
    
    def generate_pdf(self):
        """Generate PDF with file location prompt and option to open"""
        if not self.current_patient:
            QMessageBox.warning(self, "Warning", "Please select a patient first!")
            return
        
        try:
            # Ask for save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF As", 
                f"prescription_{self.current_patient['reg_no']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Get current prescription data from form
                prescription_data = self.get_current_prescription_data()
                
                # Generate PDF
                pdf_path = self.generate_prescription_pdf(prescription_data, file_path)
                
                if pdf_path and os.path.exists(pdf_path):
                    # Ask if user wants to open the PDF
                    reply = QMessageBox.question(
                        self, 
                        "PDF Generated Successfully", 
                        f"PDF generated successfully!\n\nSaved at: {pdf_path}\n\nDo you want to open the PDF now?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Open PDF with default system viewer
                        try:
                            if sys.platform == "win32":
                                os.startfile(pdf_path)
                            elif sys.platform == "darwin":
                                subprocess.run(["open", pdf_path])
                            else:
                                subprocess.run(["xdg-open", pdf_path])
                        except Exception as open_error:
                            QMessageBox.warning(self, "Open Error", 
                                              f"Failed to open PDF: {str(open_error)}\n\n"
                                              f"You can manually open the file:\n{pdf_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to generate PDF")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
    
    def print_prescription(self):
        """Print current prescription with system print dialog"""
        if not self.current_patient:
            QMessageBox.warning(self, "Warning", "Please select a patient first!")
            return
        
        try:
            # Get current prescription data from form
            prescription_data = self.get_current_prescription_data()
            
            # Generate PDF to temporary file
            pdf_path = self.generate_prescription_pdf(prescription_data)
            
            if pdf_path and os.path.exists(pdf_path):
                # Use system print dialog instead of direct printing
                printer = QPrinter(QPrinter.HighResolution)
                print_dialog = QPrintDialog(printer, self)
                print_dialog.setWindowTitle("Print Prescription")
                
                # Set some default printer options
                printer.setPageSize(QPrinter.A4)
                printer.setOrientation(QPrinter.Portrait)
                printer.setFullPage(True)
                
                if print_dialog.exec_() == QPrintDialog.Accepted:
                    # Print the PDF
                    try:
                        # For PDF printing, we'll use the system's PDF viewer
                        if sys.platform == "win32":
                            os.startfile(pdf_path, "print")
                        elif sys.platform == "darwin":
                            subprocess.run(["lp", pdf_path])
                        else:
                            subprocess.run(["lp", pdf_path])
                        
                        QMessageBox.information(self, "Print", "Prescription sent to printer!")
                        
                    except Exception as print_error:
                        QMessageBox.warning(self, "Print Error", 
                                          f"Failed to send to printer: {str(print_error)}\n\n"
                                          f"You can manually print the PDF file:\n{pdf_path}")
                
                # Clean up temporary file after a delay
                QTimer.singleShot(3000, lambda: os.unlink(pdf_path) if os.path.exists(pdf_path) else None)
                
            else:
                QMessageBox.critical(self, "Error", "Failed to generate PDF for printing")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print prescription: {str(e)}")
    
    def clear_prescription_form(self):
        """Clear prescription form"""
        self.cc_entry.clear()
        self.diagnosis_entry.clear()
        self.bp_entry.clear()
        self.pulse_entry.clear()
        self.temp_entry.clear()
        self.resp_entry.clear()
        self.spo2_entry.clear()
        self.weight_entry.clear()
        self.systemic_entry.clear()
        self.selected_investigations.clear()
        self.drugs_table.setRowCount(0)
        self.advice_entry.clear()
        self.follow_up_entry.clear()
    
    def get_current_prescription_data(self):
        """Get current prescription data from form"""
        if not self.current_patient:
            return None
        
        # Get patient info - FIXED: Use actual weight from patient data
        patient_info = (
            self.current_patient['reg_no'],
            self.current_patient['name'],
            self.current_patient['age'],
            self.current_patient['gender'],
            self.current_patient.get('weight', '0')  # FIXED: Use actual weight instead of hardcoded "0"
        )
        
        # Collect vitals with bullet points - FIXED: Keep vitals with line breaks
        vitals_data = []
        if self.bp_entry.text():
            vitals_data.append(f"• BP: {self.bp_entry.text()} mmHg")
        if self.pulse_entry.text():
            vitals_data.append(f"• Pulse: {self.pulse_entry.text()}/min")
        if self.temp_entry.text():
            vitals_data.append(f"• Temperature: {self.temp_entry.text()}°F")
        if self.resp_entry.text():
            vitals_data.append(f"• Respiratory Rate: {self.resp_entry.text()}/min")
        if self.spo2_entry.text():
            vitals_data.append(f"• SpO2: {self.spo2_entry.text()}%")
        if self.weight_entry.text():
            vitals_data.append(f"• Weight: {self.weight_entry.text()} kg")
        
        # FIXED: Join vitals with line breaks
        vitals_text = "\n".join(vitals_data)
        
        # Collect drugs data
        drugs_data = []
        for row in range(self.drugs_table.rowCount()):
            drug = {
                'formulation': self.drugs_table.item(row, 0).text(),
                'dosage': self.drugs_table.item(row, 1).text(),
                'duration': self.drugs_table.item(row, 2).text(),
                'instructions': self.drugs_table.item(row, 3).text()
            }
            drugs_data.append(drug)
        
        # Create prescription tuple
        prescription = (
            0,  # id
            self.current_patient['reg_no'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.cc_entry.toPlainText(),
            self.diagnosis_entry.toPlainText(),
            vitals_text,  # FIXED: Now uses line break separated vitals
            self.systemic_entry.toPlainText(),
            self.selected_investigations.toPlainText(),
            json.dumps(drugs_data),
            self.advice_entry.toPlainText(),
            self.follow_up_entry.text(),
            json.dumps(self.doctor_info)
        )
        
        return {
            'patient_info': patient_info,
            'prescription': prescription,
            'doctor_info': self.doctor_info
        }
    
    def load_patient_history(self):
        """Load patient prescription history"""
        try:
            patient_id = self.history_patient_combo.currentData()
            if not patient_id:
                self.history_display.clear()
                return
            
            self.cursor.execute('''
                SELECT p.*, pt.name, pt.age, pt.gender 
                FROM prescriptions p 
                JOIN patients pt ON p.patient_reg_no = pt.reg_no 
                WHERE p.patient_reg_no = ? 
                ORDER BY p.date DESC
            ''', (patient_id,))
            
            prescriptions = self.cursor.fetchall()
            
            if not prescriptions:
                self.history_display.setPlainText("No prescription history found for this patient.")
                return
            
            history_text = f"Prescription History for {prescriptions[0][13]} (Reg: {patient_id})\n"
            history_text += "=" * 60 + "\n\n"
            
            for i, prescription in enumerate(prescriptions):
                history_text += f"Prescription #{i+1} - Date: {prescription[2]}\n"
                history_text += "-" * 40 + "\n"
                
                if prescription[3]:  # CC
                    history_text += f"Chief Complaints: {prescription[3]}\n"
                
                if prescription[4]:  # Diagnosis
                    history_text += f"Diagnosis: {prescription[4]}\n"
                
                if prescription[5]:  # Vitals
                    history_text += f"Vitals: {prescription[5]}\n"
                
                # Drugs
                if prescription[8]:
                    try:
                        drugs = json.loads(prescription[8])
                        if drugs:
                            history_text += "Drugs:\n"
                            for drug in drugs:
                                history_text += f"  - {drug.get('formulation', '')}: {drug.get('dosage', '')} for {drug.get('duration', '')}\n"
                    except:
                        history_text += "Drugs: Error parsing drug data\n"
                
                if prescription[9]:  # Advice
                    history_text += f"Advice: {prescription[9]}\n"
                
                if prescription[10]:  # Follow up
                    history_text += f"Follow Up: {prescription[10]}\n"
                
                history_text += "\n" + "=" * 60 + "\n\n"
            
            self.history_display.setPlainText(history_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load patient history: {str(e)}")
    
    def select_image(self):
        """Select image file for upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.upload_image(file_path)
    
    def upload_image(self, file_path):
        """Upload patient image"""
        try:
            patient_id = self.images_patient_combo.currentData()
            if not patient_id:
                QMessageBox.warning(self, "Warning", "Please select a patient first!")
                return
            
            # Copy image to images directory
            images_dir = "patient_images"
            os.makedirs(images_dir, exist_ok=True)
            
            file_name = os.path.basename(file_path)
            new_path = os.path.join(images_dir, f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}")
            
            # Copy file
            import shutil
            shutil.copy2(file_path, new_path)
            
            # Save to database
            description = self.image_description.text().strip()
            self.cursor.execute('''
                INSERT INTO patient_images (patient_reg_no, image_path, description, date)
                VALUES (?, ?, ?, ?)
            ''', (patient_id, new_path, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conn.commit()
            self.image_description.clear()
            self.load_patient_images()
            QMessageBox.information(self, "Success", "Image uploaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload image: {str(e)}")
    
    def generate_prescription_pdf(self, prescription_data, output_path=None):
        """Generate professional PDF prescription using WeasyPrint"""
        try:
            # Create HTML content with professional layout
            html_content = self.create_prescription_html(prescription_data)
            
            # Generate PDF
            font_config = FontConfiguration()
            html = HTML(string=html_content)
            
            if output_path:
                html.write_pdf(output_path, font_config=font_config)
                return output_path
            else:
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    html.write_pdf(tmp_file.name, font_config=font_config)
                    return tmp_file.name
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")
            return None
    
    def create_prescription_html(self, prescription_data):
        """Create professional HTML content for prescription with two-column layout"""
        patient_info = prescription_data['patient_info']
        prescription = prescription_data['prescription']
        doctor_info = prescription_data['doctor_info']
        
        # Parse drugs data
        drugs_list = json.loads(prescription[8]) if prescription[8] else []
        
        # Create drugs HTML
        drugs_html = ""
        if drugs_list:
            for drug in drugs_list:
                formulation = drug.get('formulation', '')
                dosage = drug.get('dosage', '')
                duration = drug.get('duration', '')
                instructions = drug.get('instructions', '')
                
                drugs_html += f"""
                <div class="drug-item">
                    <div class="drug-formulation">{formulation}</div>
                    <div class="drug-details">{dosage}</div>
                    <div class="drug-details">{duration}</div>
                    <div class="drug-details">{instructions}</div>
                </div>
                <br>
                """
        else:
            drugs_html = "<p>No drugs prescribed</p>"
        
        # Format date and time nicely
        current_datetime = datetime.now()
        prescription_date = current_datetime.strftime("%d/%m/%Y")
        prescription_time = current_datetime.strftime("%I:%M %p")
        
        # FIXED: Format advice with proper bullets for all lines
        advice_text = prescription[9] or 'Not specified'
        if advice_text != 'Not specified':
            # Add bullet to first line and ensure all lines have bullets
            advice_lines = advice_text.split('\n')
            formatted_advice = []
            for i, line in enumerate(advice_lines):
                if line.strip():  # Only process non-empty lines
                    formatted_advice.append(f"- {line.strip()}")
            advice_display = '<br>'.join(formatted_advice)
        else:
            advice_display = 'Not specified'
        
        # Create HTML template with two-column layout
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Medical Prescription</title>
            <style>
                @page {{
                    size: A4;
                    margin: 0.5in 0.5in 0.5in 0.5in; /* 0.5 inch margins on all sides */
                }}
                
                body {{
                    font-family: 'Times New Roman', Times, serif;
                    line-height: 1.3;
                    color: #000;
                    margin: 0;
                    padding: 0;
                    font-size: 12pt;
                }}
                
                .top-spacer {{
                    height: 0.8in; /* ADDED: Space at the top to prevent cutting */
                    width: 100%;
                }}
                
                .prescription-container {{
                    width: 100%;
                    height: 100%;
                    position: relative;
                }}
                
                .header {{
                    text-align: left;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #000;
                }}
                
                .doctor-name {{
                    font-size: 18pt;  /* Increased from 14pt to 18pt (4pt more) */
                    font-weight: bold;
                    margin-bottom: 3px;
                }}
                
                .doctor-qualifications {{
                    font-size: 15pt;  /* Increased from 11pt to 15pt (4pt more) */
                    margin-bottom: 2px;
                }}
                
                .doctor-details {{
                    font-size: 14pt;  /* Increased from 10pt to 14pt (4pt more) */
                    margin-bottom: 1px;
                }}
                
                .prescription-title {{
                    text-align: center;
                    font-size: 14pt;
                    font-weight: bold;
                    margin: 10px 0;
                    text-decoration: underline;
                }}
                
                .patient-info {{
                    margin: 10px 0;
                    font-size: 13pt;  /* Increased from 11pt to 13pt (2pt more) */
                }}
                
                .content-wrapper {{
                    display: flex;
                    margin-top: 10px;
                    width: 100%;
                }}
                
                .vertical-line {{
                    border-left: 2px solid #000;
                    margin: 0 15px;
                    height: auto;
                }}
                
                .left-section {{
                    width: 30%;
                    padding-right: 10px;
                }}
                
                .right-section {{
                    width: 70%;
                    padding-left: 10px;
                }}
                
                .section {{
                    margin: 8px 0;
                    page-break-inside: avoid;
                }}
                
                .section-title {{
                    font-weight: bold;
                    margin-bottom: 3px;
                    font-size: 11pt;
                }}
                
                .section-content {{
                    margin-left: 5px;
                    font-size: 11pt;
                    word-wrap: break-word;
                }}
                
                .drug-item {{
                    margin: 5px 0;
                }}
                
                .drug-formulation {{
                    font-weight: bold;
                }}
                
                .drug-details {{
                    margin-left: 20px;
                }}
                
                .footer {{
                    margin-top: 20px;
                    text-align: right;
                    padding-top: 10px;
                    font-size: 11pt;
                }}
                
                .bangla-text {{
                    font-family: 'Times New Roman', Times, serif;
                    font-size: 11pt;
                }}
                
                .date-time {{
                    text-align: right;
                    margin-bottom: 5px;
                    font-size: 11pt;
                }}
                
                .vitals-list {{
                    margin-left: 20px;
                }}
                
                .investigations-list {{
                    margin-left: 20px;
                }}
                
                .advice-list {{
                    margin-left: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="top-spacer"></div> <!-- ADDED: This creates space at the top -->
            <div class="prescription-container">
                <div class="header">
                    <div class="doctor-name">Dr. {doctor_info['name']}</div>
                    <div class="doctor-qualifications">{doctor_info['degrees']} | {doctor_info['designation']}</div>
                    <div class="doctor-details">{doctor_info['institution']}</div>
                    <div class="doctor-details">BMDC: {doctor_info['bmdc_reg_no']} | Phone: {doctor_info['phone']}</div>
                    <div class="doctor-details">{doctor_info['address']}</div>
                </div>
                
                <div class="prescription-title">MEDICAL PRESCRIPTION</div>
                
                <div class="patient-info">
                    <strong>Name:</strong> {patient_info[1]} &nbsp;&nbsp;&nbsp;
                    <strong>Age:</strong> {patient_info[2]} &nbsp;&nbsp;&nbsp;
                    <strong>Gender:</strong> {patient_info[3]} &nbsp;&nbsp;&nbsp;
                    <strong>Weight:</strong> {patient_info[4]}kg &nbsp;&nbsp;&nbsp;
                    <strong>Reg No:</strong> {patient_info[0]} &nbsp;&nbsp;&nbsp;<br>
                    <strong>Date:</strong> {prescription_date} &nbsp;&nbsp;&nbsp;
                    <strong>Time:</strong> {prescription_time}
                </div>
                
                <div class="content-wrapper">
                    <!-- Left Section (Patient Details) - 30% width -->
                    <div class="left-section">
                        <div class="section">
                            <div class="section-title">Chief Complaint:</div>
                            <div class="section-content">{prescription[3] or 'Not specified'}</div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Vitals:</div>
                            <div class="section-content">
                                <div class="vitals-list">{prescription[5].replace('\n', '<br>') or 'Not specified'}</div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Systemic Examination:</div>
                            <div class="section-content">{prescription[6] or 'Not significant'}</div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Diagnosis:</div>
                            <div class="section-content">{prescription[4] or 'Not specified'}</div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Investigations:</div>
                            <div class="section-content">
                                <div class="investigations-list">{prescription[7].replace('\n', '<br>• ') or 'Not specified'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Vertical Line -->
                    <div class="vertical-line"></div>
                    
                    <!-- Right Section (Medications and Advice) - 70% width -->
                    <div class="right-section">
                        <div class="section">
                            <div class="section-title">Medications:</div>
                            <div class="section-content">
                                {drugs_html}
                            </div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Advice:</div>
                            <div class="section-content">
                                <div class="advice-list">{advice_display}</div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">Follow Up:</div>
                            <div class="section-content">{prescription[10] or 'Not specified'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <div>Signature: _________________________</div>
                    <div><strong>Dr. {doctor_info['name']}</strong></div>
                    <div>{doctor_info['degrees']}</div>
                    <div>{doctor_info['designation']}</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template

def main():
    app = QApplication(sys.argv)
    window = MedicalPrescriptionSystemPyQt()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
