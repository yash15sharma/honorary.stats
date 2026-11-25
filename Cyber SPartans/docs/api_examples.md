# honorary.stats — Backend API Specifications & Examples

This document contains real, verified example requests and responses for the **honorary.stats** backend.

---

## 1. POST `/api/analyze`

Extracts the worker's job role, detected skills, missing skills, and years of experience from either text or speech audio.

### A. JSON Request (Typing Mode)
**Headers:** `Content-Type: application/json`

```json
{
  "text": "I have been working as a tailor for 5 years, stitching blouses, suits and doing alterations.",
  "language": "en"
}
```

*Hindi text example:*
```json
{
  "text": "मैं 6 साल से रसोइया का काम कर रहा हूँ। मुझे दाल, करी, रोटी और तंदूर बनाना आता है।",
  "language": "hi"
}
```

### B. Multipart Form-Data Request (Voice / Audio Mode)
**Headers:** `Content-Type: multipart/form-data`

| Field | Type | Description |
| :--- | :--- | :--- |
| `audio` | File (`.mp3`, `.wav`, `.webm`, `.ogg`) | Recorded audio file |
| `language` | String (`"en"` or `"hi"`) | Spoken language |

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "audio=@recording.mp3;type=audio/mpeg" \
  -F "language=hi"
```

---

### Real Success Response (HTTP 200)

```json
{
  "transcript": "I have been working as a tailor for 5 years, stitching blouses, suits and doing alterations.",
  "role": "Tailor",
  "skills": [
    "Blouse Stitching",
    "Salwar Suit Stitching",
    "Alterations"
  ],
  "missing_skills": [
    "Embroidery",
    "Fabric Cutting & Marking",
    "Body Measurement & Sizing",
    "Sewing Machine Maintenance"
  ],
  "years_experience": 5
}
```

### Audio Unintelligible Response (HTTP 200)
Returned when background noise, silence, or unintelligible speech is uploaded so the frontend can prompt the worker to type:

```json
{
  "error": "could_not_understand",
  "message": "Please type instead"
}
```

---

## 2. GET `/api/path/{card_id}`

Returns the full personalized pathway (skill gap, next course, nearest RPL certification centre, government schemes, and a 3-sentence summary in the worker's language).

### Example 1: Hindi Worker (e.g. Tailor Sunita)
**Request:** `GET http://localhost:8000/api/path/card-tailor-hi`

```json
{
  "skill_gap": [
    "पैटर्न मेकिंग और बुटीक डिजाइनिंग",
    "कंप्यूटरीकृत कढ़ाई मशीन संचालन",
    "औद्योगिक गारमेंट फिनिशिंग और गुणवत्ता जांच"
  ],
  "next_course": {
    "title": "Advanced Garment Construction & Boutique Masterclass",
    "provider": "Skill India Digital (Apparel Sector Council)",
    "duration": "4 Weeks",
    "link": "https://www.skillindiadigital.gov.in"
  },
  "nearest_centre": {
    "name": "Pradhan Mantri Kaushal Kendra (PMKK) - RPL Apparel Centre",
    "city": "New Delhi",
    "link": "https://www.skillindiadigital.gov.in"
  },
  "schemes": [
    {
      "name": "पीएम विश्वकर्मा योजना",
      "reason": "Provides ₹15,000 modern toolkit incentive, certified skill training with ₹500/day stipend, and collateral-free enterprise loan up to ₹3 Lakhs at 5% interest.",
      "link": "https://pmvishwakarma.gov.in"
    },
    {
      "name": "स्किल इंडिया डिजिटल पूर्व शिक्षण की मान्यता (RPL)",
      "reason": "Formal government assessment recognizing informal work experience with an NSQF certificate and digital skill ID.",
      "link": "https://www.skillindiadigital.gov.in"
    }
  ],
  "summary": "आपके पास Blouse Stitching, Alterations का अच्छा व्यावहारिक हुनर और अनुभव है। अपनी कमाई बढ़ाने के लिए आपका अगला कदम पैटर्न मेकिंग और बुटीक डिजाइनिंग सीखना और Advanced Garment Construction & Boutique Masterclass पूरा करना है। आप पीएम विश्वकर्मा योजना से सरकारी सहायता और मान्यता प्राप्त प्रमाण पत्र भी ले सकते हैं।",
  "is_sample": true
}
```

---

### Example 2: English Worker (e.g. Cook Rajesh)
**Request:** `GET http://localhost:8000/api/path/card-cook-en`

```json
{
  "skill_gap": [
    "Commercial Food Safety & FSSAI Standards",
    "Continental & Multi-Cuisine Preparation",
    "Kitchen Costing & Inventory Management"
  ],
  "next_course": {
    "title": "Commercial Culinary Operations & Food Hygiene (FSSAI)",
    "provider": "Tourism & Hospitality Skill Council via Skill India",
    "duration": "3 Weeks",
    "link": "https://www.skillindiadigital.gov.in"
  },
  "nearest_centre": {
    "name": "National Council for Hotel Management RPL Hub",
    "city": "Mumbai",
    "link": "https://www.skillindiadigital.gov.in"
  },
  "schemes": [
    {
      "name": "Skill India Digital Recognition of Prior Learning (RPL)",
      "reason": "Formal government assessment recognizing informal work experience with an NSQF certificate and digital skill ID.",
      "link": "https://www.skillindiadigital.gov.in"
    },
    {
      "name": "PM SVANidhi Scheme",
      "reason": "Collateral-free working capital loan with interest subsidy and digital cashback for informal food makers, cooks, and street vendors.",
      "link": "https://www.myscheme.gov.in"
    }
  ],
  "summary": "You already possess proven practical skills in Regional Curry & Gravy Cooking, Roti, Naan & Bread Making. Your next step to boost your earnings is learning Commercial Food Safety & FSSAI Standards through the Commercial Culinary Operations & Food Hygiene (FSSAI) program. You can also access official funding and certification through Skill India Digital Recognition of Prior Learning (RPL).",
  "is_sample": true
}
```

---

### Nonexistent Card ID (HTTP 404)
**Request:** `GET http://localhost:8000/api/path/card-invalid`

```json
{
  "detail": "Skill card 'card-invalid' not found. Please verify the card ID."
}
```

---

## 3. GET `/api/health`

Verifies backend configuration and API key status:

```json
{
  "gemini": true,
  "elevenlabs": false
}
```

---

## 4. For Person C: `skill_cards` Table Contract

When Person C creates skill cards in `app/card.py`, save records directly to the `skill_cards` table in `data/honorary_stats.db`:

### Table Schema:
```sql
CREATE TABLE skill_cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    skills_json TEXT NOT NULL,
    years_experience INTEGER,
    language TEXT DEFAULT 'en',
    created_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES job_roles(id)
);
```

### Field Requirements:
- `id`: Unique string ID (e.g. `uuid.uuid4().hex[:10]` or `card-xxxx`).
- `name`: Worker's name (e.g. `"Sunita"`, `"Rajesh"`).
- `role_id`: Integer matching `job_roles.id`:
  - `1` = **Tailor**
  - `2` = **Cook**
  - `3` = **Electrician**
- `skills_json`: Serialized JSON array of **English skill names** (e.g. `'["Blouse Stitching", "Alterations"]'`).
- `years_experience`: Integer (e.g. `5`) or `NULL`.
- `language`: String (`"en"` or `"hi"`).
- `created_at`: ISO timestamp string (e.g. `datetime.utcnow().isoformat()`).

---

## 5. For Person A: Frontend Integration Notes

1. **Base URL**: `http://localhost:8000` (or `window.location.origin`).
2. **CORS**: Fully enabled for all origins (`*`), with credentials and all methods allowed.
3. **Dual Analyze Endpoint**: Send either a simple JSON payload (`{"text": "...", "language": "hi"}`) or `FormData` with an audio blob (`formData.append("audio", blob, "voice.webm")`).
4. **Card & Path Flow**:
   - `POST /api/analyze` -> displays detected skills for worker confirmation.
   - `POST /api/card` (Person C) -> returns `{ "card_id": "..." }`.
   - `GET /api/path/{card_id}` -> populates the "Your path" screen with next-level skills, course, centre, and schemes.
