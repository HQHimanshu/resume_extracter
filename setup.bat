@echo off
echo Resume Parser - Windows Setup
echo =====================================
echo.

echo Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Step 1: Checking Tesseract OCR installation...
where tesseract >nul 2>nul
if errorlevel 1 (
    echo ❌ Tesseract OCR not found in PATH
    echo.
    echo Please install Tesseract OCR from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Important: Check "Add to PATH" during installation
    echo Default install path: C:\Program Files\Tesseract-OCR
    echo.
    echo After installation, restart this script
    pause
    exit /b 1
)

echo ✅ Tesseract found

echo.
echo Step 2: Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo Step 3: Activating virtual environment...
call venv\Scripts\activate

echo.
echo Step 4: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 5: Installing Python packages...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo Creating requirements.txt...
    echo Flask==2.3.3 > requirements.txt
    echo pdfplumber==0.10.2 >> requirements.txt
    echo pytesseract==0.3.10 >> requirements.txt
    echo PyMuPDF==1.23.8 >> requirements.txt
    echo Pillow==10.0.0 >> requirements.txt
    pip install -r requirements.txt
)

echo.
echo Step 6: Verifying installations...
echo Installed packages:
pip list | findstr "Flask pdfplumber pytesseract PyMuPDF Pillow"

echo.
echo Step 7: Testing Tesseract...
python -c "import pytesseract; print('✅ pytesseract imported'); print('Tesseract path:', pytesseract.pytesseract.tesseract_cmd)"

echo.
echo Step 8: Testing all imports...
python -c "
import flask
import pdfplumber
import pytesseract
import fitz
from PIL import Image
print('✅ All imports successful')
print(f'   Flask: {flask.__version__}')
print(f'   pdfplumber: {pdfplumber.__version__}')
print(f'   pytesseract: {pytesseract.__version__}')
print(f'   PyMuPDF: {fitz.version}')
print(f'   Pillow: {Image.__version__}')
"

echo.
echo 🎉 Setup complete!
echo =====================================
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Run the Flask application:
echo    python app.py
echo.
echo 3. Open your browser and go to:
echo    http://localhost:5000
echo.
echo 4. Upload a resume file to test the parser
echo.
echo ❓ Troubleshooting:
echo    - If you get Tesseract errors, update the path in resume_parser/extractor.py
echo    - The default path is: C:\Program Files\Tesseract-OCR\tesseract.exe
echo.
pause