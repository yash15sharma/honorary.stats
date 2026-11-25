# honorary.stats (SkillPath)

> **Voice-first skills recognition & career pathway generator for informal workers in India.**
> Hackathon DEMO prototype built for informal workers (Tailor, Cook, Electrician) in English and Hindi.

---

## 📁 Team Folder Structure & Responsibilities

| Teammate | Assigned Files | Responsibilities |
| :--- | :--- | :--- |
| **Person B** *(Current)* | `app/main.py`, `app/db.py`, `app/ai.py`, `app/path.py`, `data/seed.py`, `docs/`, `tests/` | Backend core, SQLite database, Gemini analysis, career pathways |
| **Person C** | `app/card.py`, `app/voice.py`, `README.md` | Skill card generation, QR code image, ElevenLabs / gTTS audio |
| **Person A** | `app/static/` | React (via CDN) + HTML/CSS frontend UI |

---

## 🛠️ Tech Stack & Requirements

- **Python**: 3.11+
- **Backend**: FastAPI, Uvicorn, Python-Dotenv, Python-Multipart
- **Database**: SQLite (`data/honorary_stats.db`)
- **AI & LLM**: Google Gemini API (`google-genai`)
- **Voice**: ElevenLabs API (with fallback to `gTTS`)
- **QR Codes**: `qrcode[pil]`
- **Frontend**: Plain HTML5, Tailwind / custom CSS, React via CDN (no npm build)

---

## 📋 API Contract

| Method | Endpoint | Request Payload | Response Shape |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/analyze` | JSON `{text, language}` **OR** multipart form `{audio, language}` | `{transcript, role, skills:[str], missing_skills:[str], years_experience:int\|null}` |
| **POST** | `/api/card` | JSON `{name, role, skills:[str], years_experience:int, language}` | `{card_id}` |
| **GET** | `/api/card/{id}` | None | `{card_id, name, role, skills:[str], years_experience, language}` |
| **GET** | `/api/card/{id}/qr.png` | None | PNG Image |
| **GET** | `/card/{id}` | None | Printable HTML card view |
| **GET** | `/api/path/{card_id}` | None | `{skill_gap:[str], next_course:{title,provider,duration,link}, nearest_centre:{name,city,link}, schemes:[{name,reason,link}], summary:str, is_sample:true}` |
| **POST** | `/api/speak` | JSON `{text, language}` | `audio/mpeg` audio stream |
| **GET** | `/api/health` | None | `{gemini: bool, elevenlabs: bool}` |

---

## 🚀 Getting Started

### 1. Setup Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys (optional: fallbacks are included so the app never crashes without keys):
```powershell
copy .env.example .env
```

### 4. Seed the Database
```powershell
python data/seed.py
```

### 5. Run Development Server
```powershell
uvicorn app.main:app --reload --port 8000
```
- Web Application: [http://localhost:8000](http://localhost:8000)
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🧪 Running Tests

Run the full scenario suite verifying both text and audio analysis, multilingual pathways (Hindi & English), fallbacks, and 404 handlers:
```powershell
python tests/run_scenarios.py
```
