#!/usr/bin/env python3
"""
Simple script to reset the database and create test users.
Run this if you're having login issues.
"""

import os
from app import app, db
from models import User, create_hardcoded_users, create_question_banks

def reset_database():
    """Reset database and create fresh users."""
    print("🔄 Resetting database...")
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✅ All tables dropped")
        
        # Create all tables
        db.create_all()
        print("✅ All tables created")
        
        # Create hardcoded users
        create_hardcoded_users()
        print("✅ Test users created")
        
        # Create question banks
        create_question_banks()
        print("✅ Question banks created")
        
        # Verify users exist
        admin = User.query.filter_by(email='admin@lddetector.com').first()
        counselor = User.query.filter_by(email='counselor@lddetector.com').first()
        
        if admin and counselor:
            print("✅ Admin and Counselor users verified")
            print(f"   Admin: {admin.email} (role: {admin.role})")
            print(f"   Counselor: {counselor.email} (role: {counselor.role})")
        else:
            print("❌ Failed to create test users")
            return False
    
    print("\n🎉 Database reset complete!")
    print("📝 You can now login with:")
    print("   Admin: admin@lddetector.com / admin123")
    print("   Counselor: counselor@lddetector.com / counselor123")
    return True

if __name__ == '__main__':
    reset_database()
