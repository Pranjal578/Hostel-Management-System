#!/bin/bash

# Hostel Management System - Setup Script
# This script automates the installation and setup process

echo "=================================="
echo "🏠 Hostel Management System Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python is installed"
echo ""

# Create virtual environment (optional but recommended)
read -p "Do you want to create a virtual environment? (y/n): " create_venv

if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "✅ Virtual environment created and activated"
    echo ""
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create necessary directories
echo "Creating required directories..."
mkdir -p static/images static/qr

echo "✅ Directories created"
echo ""

# Initialize database
echo "Initializing database..."
python3 << END
from app import app, db
with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully")
END

echo ""

# Display completion message
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To run the application:"
echo ""
if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "1. Activate virtual environment (if not already active):"
    echo "   source venv/bin/activate"
    echo ""
fi
echo "2. Start the server:"
echo "   python app.py"
echo ""
echo "3. Open your browser and go to:"
echo "   http://localhost:5000"
echo ""
echo "Default Admin Credentials:"
echo "   Username: demo"
echo "   Password: demo"
echo ""
echo "⚠️  IMPORTANT: Change admin password in production!"
echo ""
echo "=================================="
