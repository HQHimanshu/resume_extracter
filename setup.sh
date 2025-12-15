#!/bin/bash

# Resume Parser - Setup Script
# This script installs system dependencies and sets up the Python environment

set -e  # Exit on error

echo "🚀 Starting Resume Parser AI setup..."
echo "====================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ "$python_version" < "3.8" ]]; then
    echo "❌ Python 3.8+ is required. Found Python $python_version"
    echo "📥 Please install Python 3.8 or higher from https://python.org"
    exit 1
fi
echo "✅ Python $python_version detected"

# Detect operating system
echo "🔍 Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "✅ Linux detected"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "✅ macOS detected"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "❌ Windows detected"
    echo "📝 For Windows, please run the following commands manually:"
    echo ""
    echo "1. Install Tesseract OCR from:"
    echo "   https://github.com/UB-Mannheim/tesseract/wiki"
    echo "   Make sure to check 'Add to PATH' during installation"
    echo ""
    echo "2. Create virtual environment:"
    echo "   python -m venv venv"
    echo "   venv\\Scripts\\activate"
    echo ""
    echo "3. Install Python packages:"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "4. Update Tesseract path in extractor.py if needed:"
    echo "   pytesseract.pytesseract.tesseract_cmd = r\"C:\\Program Files\\Tesseract-OCR\\tesseract.exe\""
    exit 1
else
    echo "❌ Unknown operating system: $OSTYPE"
    exit 1
fi

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."

if [[ "$OS" == "linux" ]]; then
    echo "🔄 Updating package list..."
    sudo apt-get update
    
    echo "📥 Installing Tesseract OCR..."
    sudo apt-get install -y tesseract-ocr
    
    echo "📥 Installing Tesseract development libraries..."
    sudo apt-get install -y libtesseract-dev
    
    echo "📥 Installing Python development tools..."
    sudo apt-get install -y python3-dev python3-pip python3-venv build-essential
    
elif [[ "$OS" == "macos" ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "🔄 Updating Homebrew..."
    brew update
    
    echo "📥 Installing Tesseract OCR..."
    brew install tesseract
    
    echo "📥 Installing pkg-config for image libraries..."
    brew install pkg-config
fi

# Verify Tesseract installation
echo ""
echo "🔍 Verifying Tesseract installation..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n 1)
    echo "✅ Tesseract installed: $tesseract_version"
else
    echo "❌ Tesseract installation failed"
    exit 1
fi

# Create virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."

if [[ ! -d "venv" ]]; then
    echo "📁 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📁 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo ""
echo "📦 Installing Python packages from requirements.txt..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found. Creating from hardcoded dependencies..."
    cat > requirements.txt << EOF
Flask==2.3.3
pdfplumber==0.10.2
pytesseract==0.3.10
PyMuPDF==1.23.8
Pillow==10.0.0
EOF
    pip install -r requirements.txt
fi

# Verify installations
echo ""
echo "🔍 Verifying Python package installations..."
echo "📊 Installed packages:"
pip list | grep -E "Flask|pdfplumber|pytesseract|PyMuPDF|Pillow"

# Test Tesseract in Python
echo ""
echo "🧪 Testing Tesseract Python bindings..."
python3 -c "
import pytesseract
import sys
try:
    print('✅ pytesseract imported successfully')
    print(f'   Tesseract path: {pytesseract.pytesseract.tesseract_cmd}')
except Exception as e:
    print(f'❌ Error importing pytesseract: {e}')
    sys.exit(1)
"

# Create a test script to verify all imports
echo ""
echo "🧪 Testing all imports..."
cat > test_imports.py << 'EOF'
import sys
import flask
import pdfplumber
import pytesseract
import fitz
from PIL import Image

print("✅ All imports successful:")
print(f"   Flask: {flask.__version__}")
print(f"   pdfplumber: {pdfplumber.__version__}")
print(f"   pytesseract: {pytesseract.__version__}")
print(f"   PyMuPDF (fitz): {fitz.version}")
print(f"   Pillow (PIL): {Image.__version__}")
EOF

python3 test_imports.py
rm -f test_imports.py

echo ""
echo "🎉 Setup complete!"
echo "====================================="
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the Flask application:"
echo "   python app.py"
echo ""
echo "3. Open your browser and go to:"
echo "   http://localhost:5000"
echo ""
echo "4. Upload a resume file to test the parser"
echo ""
echo "🛠️  For development:"
echo "   - Always activate the virtual environment first"
echo "   - Add new dependencies to requirements.txt:"
echo "     pip freeze > requirements.txt"
echo ""
echo "❓ Troubleshooting:"
echo "   - If Tesseract is not found, update the path in resume_parser/extractor.py"
echo "   - Check that files are in standard formats (PDF, DOCX, PNG, JPG)"
echo "   - Ensure uploaded files are under 10MB"
echo ""