# 🚀 Simple Start Guide

## Just Want to Run the App? Here's How:

### 1. Install Dependencies (One Time)
```bash
pip install -r requirements.txt
```

### 2. Start the App
```bash
python start_app.py
```

### 3. Open Your Browser
Go to: http://localhost:5000

### 4. Login
- **Admin**: admin@lddetector.com / admin123
- **Counselor**: counselor@lddetector.com / counselor123

## That's It! 🎉

---

## If Something Goes Wrong:

### Login Issues?
```bash
python reset_database.py
python start_app.py
```

### Still Having Problems?
```bash
# Check if everything is working
python test_local_setup.py
```

---

## What You Can Do:

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

---

## Files You Need:
- `start_app.py` - Start the app
- `reset_database.py` - Fix login issues
- `requirements.txt` - Dependencies

Everything else is just extra! 😊
