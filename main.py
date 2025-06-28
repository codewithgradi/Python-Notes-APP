from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox, QLabel, QTextEdit, QPushButton, 
    QFrame, QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit, QScrollArea,
    QInputDialog
)
from PyQt5 import QtGui
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
import sys

class NotesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.setWindowTitle("Notes App")
        self.resize(600, 600)

        # Initialize note tracking
        self.notes_number = 0
        self.note_frames = []  # List to store note frames
        self.db = None  # Database connection

        # Initialize UI
        self.init_ui()
        # Initialize database
        self.init_db()
        # Load notes from database
        self.load_notes()

    def init_ui(self):
        """Initialize all UI components"""
        # Main widgets
        self.dots = QLabel("📑")
        self.dark_light_mode = QCheckBox()
        self.main_title = QLabel("All Notes")
        self.number_of_notes = QLabel("0 notes")
        self.search_value = QLineEdit()
        self.search_value.setPlaceholderText("Search notes...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_notes)  # Add this line
        self.search_btn.setStyleSheet("background-color:#88dbf2;padding:7px;font-weight:bold;")
        self.add_new_note = QPushButton("+ Add New Note")
        self.add_new_note.clicked.connect(self.add_note)
        self.add_new_note.setStyleSheet("background-color:#88dbf2;padding:5px;font-weight:bold;")

        # Main layout structure
        main_layout = QVBoxLayout()
        
        # Header section
        header_layout = QVBoxLayout()
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.dots)
        title_layout.addWidget(self.main_title)
        title_layout.addWidget(self.number_of_notes)
        title_layout.addWidget(self.dark_light_mode)
        self.dots.setStyleSheet("font-size:30px;")
        self.main_title.setStyleSheet("font-size:20px;color:#505081;")
        self.number_of_notes.setStyleSheet("font-size:20px;color:#505081;")
        self.dark_light_mode.setStyleSheet("font-size:20px;color:#505081;")
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_value)
        search_layout.addWidget(self.search_btn)
        header_layout.addLayout(title_layout)
        header_layout.addLayout(search_layout)        
        main_layout.addLayout(header_layout)

        # Main scroll area for notes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Container for note frames
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.setAlignment(Qt.AlignTop)
        self.notes_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.notes_container)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.add_new_note)
        
        self.setLayout(main_layout)

        # Styles
        self.setStyleSheet("background-color:White;")
        self.notes_container.setStyleSheet("""
            background-color:#ffffff;
            font-size:12px; 
        """)
        self.search_value.setStyleSheet("background-color:white;color:black;font-size:12px;padding:5px;")

    def init_db(self):
        """Initialize database connection"""
        # Remove any existing connection
        if QSqlDatabase.contains("qt_sql_default_connection"):
            QSqlDatabase.removeDatabase("qt_sql_default_connection")
            
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("notesapp.db")
        
        if not self.db.open():
            QMessageBox.critical(self, "Database Error", 
                               f"Could not open database: {self.db.lastError().text()}")
            sys.exit(1)
            
        # Enable foreign keys
        query = QSqlQuery(self.db)
        query.exec_("PRAGMA foreign_keys = ON;")

    def create_note_frame(self, title, content, date, notes_id=None):
        """Creates a single note frame with all components"""
        note_frame = QFrame()
        note_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        note_frame.setLineWidth(1)
        note_frame.setStyleSheet("background-color:#fff1ff;")
        
        # Frame layout
        frame_layout = QVBoxLayout(note_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top row (title and date)
        top_layout = QHBoxLayout()
        note_title = QLabel(title)
        note_title.setStyleSheet("font-weight: bold;color:black;")
        created_on = QLabel(date)
        created_on.setStyleSheet("color: black;")
        top_layout.addWidget(note_title)
        top_layout.addStretch()
        top_layout.addWidget(created_on)
        
        # Middle (text edit with scroll)
        text_edit = QTextEdit()
        text_edit.setStyleSheet("background-color:white;color:black;font-style:italic;")
        text_edit.setPlainText(content)
        text_edit.setMinimumHeight(150)
        
        # Bottom (buttons)
        bottom_layout = QHBoxLayout()
        notes_id_label = QLabel(str(notes_id) if notes_id else "New")
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.remove_note(note_frame))
        delete_btn.setStyleSheet("background-color:rgb(200,0,0);color:white;")
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(lambda: self.update_existing_note(note_frame))
        update_btn.setStyleSheet("background-color:green;color:white;")
        bottom_layout.addWidget(notes_id_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(update_btn)
        bottom_layout.addWidget(delete_btn)
        
        # Add to frame
        frame_layout.addLayout(top_layout)
        frame_layout.addWidget(text_edit)
        frame_layout.addLayout(bottom_layout)
        
        # Add to container
        self.notes_layout.addWidget(note_frame)
        self.note_frames.append({
            'frame': note_frame,
            'title': note_title,
            'content': text_edit,
            'date': created_on,
            'id': notes_id_label
        })
        
        return note_frame

    # ... (rest of initialization)

    # Then add the search method:
    def search_notes(self):
        """Search for notes containing the search term in content or title"""
        search_term = self.search_value.text().strip()
        
        if not search_term:
            # If search is empty, reload all notes
            self.clear_notes_display()
            self.load_notes()
            return
        
        # Clear current display
        self.clear_notes_display()
        
        # Prepare search query (using LIKE with wildcards)
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT * FROM notes 
            WHERE note LIKE ? OR note_title LIKE ?
            ORDER BY created_on DESC
        """)
        query.addBindValue(f"%{search_term}%")
        query.addBindValue(f"%{search_term}%")
        
        if not query.exec_():
            QMessageBox.warning(self, "Search Error", 
                            f"Failed to search notes: {query.lastError().text()}")
            return
        
        # Display search results
        found_count = 0
        while query.next():
            notes_id = query.value(0)
            date_made = query.value(1)
            note = query.value(2)
            title = query.value(3)
            
            self.create_note_frame(title, note, date_made, notes_id)
            found_count += 1
        
        self.number_of_notes.setText(f"{found_count} notes found")
        
        if found_count == 0:
            QMessageBox.information(self, "Search Results", 
                                "No notes found matching your search")

    def clear_notes_display(self):
        """Clear all notes from the display"""
        for note in self.note_frames:
            note['frame'].deleteLater()
        self.note_frames = []
        self.notes_number = 0

    def load_notes(self):
        """Loads notes from the database"""
        query = QSqlQuery(self.db)
        if not query.exec_("SELECT * FROM notes"):
            QMessageBox.critical(self, "Error", f"Failed to load notes: {query.lastError().text()}")
            return
            
        while query.next():
            notes_id = query.value(0)
            date_made = query.value(1)
            note = query.value(2)
            title = query.value(3)
            
            self.create_note_frame(title, note, date_made, notes_id)
            self.notes_number += 1
        
        self.number_of_notes.setText(f"{self.notes_number} notes")

    def add_note(self):
        """Adds a new note with actual content"""
        title, ok = QInputDialog.getText(self, "New Note", "Enter the Notes Title:")
        if not ok or not title:
            return
            
        content, ok = QInputDialog.getMultiLineText(
            self, "New Note", "Enter your note content:")
        if not ok:
            return
            
        date = QDate.currentDate().toString(Qt.ISODate)
        self.create_note_frame(title, content, date)
        self.notes_number += 1
        self.number_of_notes.setText(f"{self.notes_number} notes")

        # Save to database
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO notes (created_on, note, note_title, user_id, last_updated)
            VALUES (?, ?, ?, 1, ?)
        """)
        query.addBindValue(date)
        query.addBindValue(content)
        query.addBindValue(title)
        query.addBindValue(date)
        
        if not query.exec_():
            QMessageBox.critical(self, "Error", f"Failed to save note: {query.lastError().text()}")

    def remove_note(self, frame):
        """Removes a note from the UI and database"""
        for note in self.note_frames:
            if note['frame'] == frame:
                # Delete from database
                query = QSqlQuery(self.db)
                query.prepare("DELETE FROM notes WHERE notes_id = ?")
                query.addBindValue(note['id'].text())
                
                if not query.exec_():
                    QMessageBox.critical(self, "Error", f"Failed to delete note: {query.lastError().text()}")
                    return
                
                # Remove from UI
                frame.deleteLater()
                self.note_frames.remove(note)
                self.notes_number -= 1
                self.number_of_notes.setText(f"{self.notes_number} notes")
                break

    def update_existing_note(self, frame):
        """Updates an existing note in the database with current content"""
        for note in self.note_frames:
            if note['frame'] == frame:
                # Get current values from UI
                note_id = note['id'].text()
                current_title = note['title'].text()
                current_content = note['content'].toPlainText()
                current_date = QDate.currentDate().toString(Qt.ISODate)
                
                # Update database
                query = QSqlQuery(self.db)
                query.prepare("""
                    UPDATE notes 
                    SET note = ?, 
                        note_title = ?,
                        last_updated = ?
                    WHERE notes_id = ?
                """)
                query.addBindValue(current_content)
                query.addBindValue(current_title)
                query.addBindValue(current_date)
                query.addBindValue(note_id)
                
                if not query.exec_():
                    QMessageBox.critical(self, "Error", f"Failed to update note: {query.lastError().text()}")
                    return
                
                # Update UI date display
                note['date'].setText(current_date)
                
                QMessageBox.information(self, "Success", "Note updated successfully!")
                break

    def closeEvent(self, event):
        """Handle application close"""
        if self.db and self.db.isOpen():
            self.db.close()
        QSqlDatabase.removeDatabase("qt_sql_default_connection")
        event.accept()

def create_database():
    """Creates and initializes the database"""
    # Remove any existing connection first
    if QSqlDatabase.contains("qt_sql_default_connection"):
        QSqlDatabase.removeDatabase("qt_sql_default_connection")
    
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("notesapp.db")
    
    if not db.open():
        error = db.lastError().text()
        QMessageBox.critical(None, "Database Error", 
                           f"Could not open database: {error}")
        sys.exit(1)
    
    query = QSqlQuery(db)
    # Enable foreign keys
    query.exec_("PRAGMA foreign_keys = ON;")
    
    # Create table
    sql = """
    CREATE TABLE IF NOT EXISTS notes(
        notes_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_on TEXT,
        note TEXT,
        note_title TEXT,
        user_id INTEGER NOT NULL,
        last_updated TEXT
    )
    """
    
    if not query.exec_(sql):
        error = query.lastError().text()
        QMessageBox.critical(None, "Database Error", 
                           f"Failed to create table: {error}")
        db.close()
        sys.exit(1)
    
    db.close()
    QSqlDatabase.removeDatabase("qt_sql_default_connection")

if __name__ == '__main__':
    app = QApplication([])
    create_database()
    main_window = NotesApp()
    main_window.show()
    app.exec_()