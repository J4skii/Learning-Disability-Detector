# Learning Disability Detector

A simple Flask web application to help detect learning disabilities through assessments.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the App
```bash
python start_app.py
```

### 3. Open Browser
Go to: http://localhost:5000

### 4. Login
- **Admin**: admin@lddetector.com / admin123
- **Counselor**: counselor@lddetector.com / counselor123

## 📝 Features

- **Dyslexia Assessment** - Reading and language evaluation
- **Dyscalculia Assessment** - Math ability evaluation  
- **Memory Assessment** - Memory recall testing
- **Flash Card Test** - Quick recognition assessment
- **User Management** - Student, counselor, admin roles
- **Progress Tracking** - Individual progress monitoring
- **Data Export** - CSV export functionality

## 🔧 If Something Goes Wrong

### Login Issues?
```bash
python reset_database.py
python start_app.py
```

## 📁 Main Files

- `start_app.py` - Start the application
- `reset_database.py` - Fix database issues
- `app.py` - Main application code
- `models.py` - Database models
- `ld_logic.py` - Assessment logic
- `requirements.txt` - Dependencies

## 🎯 What You Can Do

### As Admin:
- View all student results
- Export data
- Manage the system

### As Counselor:
- View students
- Add/remove programs and assessments
- Monitor progress

### As Student (Sign Up):
- Take assessments
- View results
- Track progress

That's it! Simple and clean. 🎉