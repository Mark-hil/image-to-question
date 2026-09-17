# 🎯 QGen AI: Multimodal Assessment & Question Bank Platform

A full-stack, enterprise-grade AI assessment generation platform that extracts text and complex diagrams from photos, textbook PDFs, and PowerPoint slide decks, enhances content, and generates pedagogy-aligned question banks (MCQs, True/False, Short Answer).

## 🚀 **Key Features**

- **🤖 Multimodal Vision & OCR Engine**: Advanced OCR with error correction combined with Groq Vision LLMs to extract handwritten, printed, and complex diagrammatic educational material.
- **🎓 Dual Pedagogical Generation Modes**:
  - **Exam Assessment Mode (`exam`)**: Summative test rigor with plausible distractors targeting student misconceptions and scenario-based questions to prevent rote guessing.
  - **Study & Practice Mode (`practice`)**: Formative self-study with active recall, foundational definitions, and rich encouraging rationales.
- **🧠 Bloom's Taxonomy Classification**: Tags and filters questions across cognitive levels (*Remember*, *Understand*, *Apply*, *Analyze*, *Evaluate*, *Create*).
- **🔒 "Extract & Discard" Privacy Architecture**: Zero-retention transient file processing. Documents are processed in-memory/temp files and immediately unlinked from disk upon OCR extraction for full FERPA/GDPR compliance.
- **📊 Quiz Bank Library & LMS Exports**: Save, organize, and export quizzes directly into Microsoft Word (`.docx`) and Canvas / Moodle QTI (`.zip`) format.
- **⚡ Async Background Processing Queue**: Fast async job execution (`/api/tasks/generate-async`) for large PDFs (up to 200+ pages) with live stage progression polling.
- **🔑 B2B Developer API Portal**: Self-service API Key generation (`qg_live_...`), prefix storage, key revocation, and interactive code snippets on the `/developer` dashboard.
- **💳 Automated Paystack Billing**: Tiered educator plans (Free, Pro, Team, Institution) and B2B API credit packs with HMAC-verified webhook upgrades.

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

## 📖 **API Usage & Monetization**

For complete API specifications, see **[API Documentation](API_DOCUMENTATION.md)** or open **`http://localhost:8000/docs`** for interactive Swagger documentation.

### 🔄 **Monetization & Quota Enforcement Flow**

```mermaid
graph TD
    Req[Incoming Generation Request] --> AuthCheck{Auth Method?}
    AuthCheck -- JWT Bearer Token --> CheckUser{Check User Tier & Quota}
    AuthCheck -- X-API-Key Header --> CheckTenant{Check API Credit Balance}
    AuthCheck -- Unauthenticated --> CheckGuest{Guest Limit: 3 uses}

    CheckUser -- Used >= Limit --> BlockUser["❌ 402 PLAN_LIMIT_REACHED<br/>(Upgrade to Pro via Paystack)"]
    CheckTenant -- Quota <= 0 --> BlockTenant["❌ 402 QUOTA_EXHAUSTED<br/>(Top up API credits)"]
    CheckGuest -- Exceeded --> BlockGuest["❌ Prompt Sign In / Register"]

    CheckUser -- Quota OK --> RunGen[Generate Questions with Vision LLM]
    CheckTenant -- Quota OK --> RunGen
    CheckGuest -- Quota OK --> RunGen

    RunGen --> Deduct["✅ Deduct Quota<br/>(User: +1 used / Tenant: -1 credit)"]
    Deduct --> ReturnResult[Return Structured Questions JSON]

    Pay["💳 Paystack Checkout<br/>(/api/billing/initialize)"] --> Hook["Webhook Handler<br/>(charge.success)"]
    Hook --> Upgrade["Auto-Upgrade Account<br/>(User: Pro 300/mo / Tenant: +10k credits)"]
```

### **1. Register Free API Key ($0.00 / 1,000 sandbox generations)**
```bash
curl -X POST "http://localhost:8000/api/tenants/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Learning App",
    "email": "dev@mylearningapp.com",
    "tier": "starter"
  }'
```

### **2. Upload Image/PDF & Generate Questions**
```bash
curl -X POST "http://localhost:8000/api/generate/upload-and-generate" \
  -H "X-API-Key: qg_live_your_secret_api_key" \
  -F "files=@your_image.png" \
  -F "qtype=mcq" \
  -F "difficulty=medium" \
  -F "num_questions=5"
```

### **3. Check Usage & Quota Balance**
```bash
curl -X GET "http://localhost:8000/api/tenants/{tenant_id}/usage"
```

### **4. Upgrade Plan or Top Up via Paystack**
```bash
curl -X POST "http://localhost:8000/api/billing/initialize" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@school.edu",
    "amount": 15.0,
    "user_id": "your_user_id",
    "plan_tier": "pro"
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