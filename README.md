# 🎯 Question Generation Project

A comprehensive OCR and question generation system that extracts text from images/PDFs, enhances it professionally, and generates educational questions.

## 🚀 **Features**

- **🔧 Ultimate OCR Service** - Advanced text extraction with error correction
- **📚 Professional Book Editor** - Text enhancement without meaning changes
- **🤖 Question Generation** - Educational content creation using AI
- **📊 Complete Pipeline** - From image to questions seamlessly
- **🎯 Conservative Editing** - Preserves original meaning while improving quality

## 📋 **Prerequisites**

- Python 3.10+
- PostgreSQL database
- Tesseract OCR
- Groq API key (for question generation)

## 🛠️ **Setup Instructions**

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd question-gen
```

### **2. Create Virtual Environment**
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### **4. Install Tesseract OCR**

#### **Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

#### **macOS:**
```bash
brew install tesseract
```

#### **Windows:**
1. Download Tesseract from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Add Tesseract to PATH
3. Set environment variable: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`

### **5. Set Up Environment Variables**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/qgen_db

# Groq API (for question generation)
GROQ_API_KEY=your_groq_api_key_here

# Tesseract OCR (optional if installed globally)
TESSERACT_CMD=/usr/bin/tesseract

# OCR Engine (optional)
OCR_ENGINE=tesseract
```

### **6. Set Up Database**

#### **Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Windows
# Download and install from postgresql.org
```

#### **Create Database:**
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell
CREATE DATABASE qgen_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE qgen_db TO your_username;
\q
```

#### **Run Migrations:**
```bash
# Initialize database (first time)
alembic upgrade head
```

### **7. Create Uploads Directory**
```bash
mkdir uploads
chmod 755 uploads
```

## 🚀 **Running the Application**

### **Development Server**
```bash
# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Production Server**
```bash
# Using gunicorn (recommended)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker
docker build -t question-gen .
docker run -p 8000:8000 question-gen
```

## 📖 **API Usage**

### **Upload and Process Image**
```bash
curl -X POST "http://localhost:8000/api/upload-and-generate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_image.png" \
  -F "qtype=mcq" \
  -F "difficulty=medium" \
  -F "num_questions=5"
```

### **Generate Questions from Text**
```bash
curl -X POST "http://localhost:8000/api/generate-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text content here...",
    "qtype": "mcq",
    "difficulty": "medium",
    "num_questions": 3
  }'
```

## 🧪 **Testing**

### **Run All Tests**
```bash
# Using pytest (recommended)
pip install pytest
pytest tests/

# Or run individual test
python -m tests.test_ocr_detailed
```

### **Test OCR Service**
```bash
python -c "
import asyncio
from services.ultimate_ocr_service import extract_text_from_path

async def test():
    result = await extract_text_from_path('uploads/your_image.png')
    print(result['text'])

asyncio.run(test())
"
```

### **Test Question Generation**
```bash
python -c "
import asyncio
from services.qgen_service import generate_questions_from_content

async def test():
    questions = generate_questions_from_content(
        text='Your text here...',
        qtype='mcq',
        difficulty='medium',
        num_questions=3
    )
    print(questions)

asyncio.run(test())
"
```

## 📁 **Project Structure**

```
question-gen/
├── services/              # Active services
│   ├── ultimate_ocr_service.py      # Main OCR service
│   ├── professional_book_editor.py  # Text editing
│   ├── qgen_service.py              # Question generation
│   ├── vision_service.py            # Image analysis
│   ├── pdf_service.py               # PDF processing
│   ├── ocr_service.py               # Basic OCR
│   └── diagram_utils.py             # Utilities
├── tests/                 # All test files
├── debug/                 # Debug tools and images
├── ocr-tools/             # OCR analysis utilities
├── docs/                  # Documentation
│   ├── guides/            # How-to guides
│   ├── organization/      # Project structure docs
│   └── success/           # Achievement documentation
├── routers/               # API routes
├── models/                # Database models
├── main.py                # Application entry
├── README.md              # This file
└── Configuration files
```

## 🔧 **Configuration**

### **OCR Settings**
- **Engine:** Tesseract (default) or PaddleOCR
- **Confidence:** High, medium, or low
- **Processing:** Async for better performance

### **Question Generation**
- **Provider:** Groq (LLaMA 3.1)
- **Types:** MCQ, True/False, Short Answer
- **Difficulty:** Easy, Medium, Hard
- **Subjects:** Any educational subject

### **Database**
- **Type:** PostgreSQL
- **Migrations:** Alembic
- **Models:** SQLAlchemy

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Tesseract Not Found**
```bash
# Check if Tesseract is installed
tesseract --version

# If not found, install or set TESSERACT_CMD environment variable
export TESSERACT_CMD=/path/to/tesseract
```

#### **Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U your_username -d qgen_db
```

#### **Import Errors**
```bash
# Ensure you're in the project root
cd /path/to/question-gen

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

#### **Groq API Issues**
```bash
# Check if API key is set
echo $GROQ_API_KEY

# Test API connection
python -c "
from services.qgen_service import generate_questions_from_content
print('API connection working')
"
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
uvicorn main:app --reload --log-level debug
```

## 📚 **Documentation**

- **[Documentation Index](docs/README.md)** - Complete documentation
- **[Guides](docs/guides/)** - How-to guides and rules
- **[Organization](docs/organization/)** - Project structure
- **[Success Stories](docs/success/)** - Achievement documentation

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 **Support**

For issues and questions:
1. Check the [troubleshooting section](#-troubleshooting)
2. Review the [documentation](docs/)
3. Check existing [issues](../../issues)
4. Create a new issue with detailed information

---

## 🚀 **Quick Start**

```bash
# 1. Clone and setup
git clone <repo-url> && cd question-gen
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys and database URL

# 3. Setup database
createdb qgen_db
alembic upgrade head

# 4. Run the server
uvicorn main:app --reload

# 5. Test it
curl -X POST "http://localhost:8000/api/upload-and-generate" \
  -F "file=@test_image.png" \
  -F "qtype=mcq" \
  -F "difficulty=medium" \
  -F "num_questions=3"
```

**Your question generation system is ready to use!** 🎉