import sys
from pathlib import Path

# Add project root to sys.path so app modules import cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection, init_db

# ==============================================================================
# SAMPLE DATA DEFINITION (Pure data-driven; add new roles/skills here without code changes)
# ==============================================================================

SEED_DATA = {
    # 1. Job Roles
    "job_roles": [
        {"name": "Tailor", "name_hi": "दर्जी"},
        {"name": "Cook", "name_hi": "रसोइया"},
        {"name": "Electrician", "name_hi": "इलेक्ट्रीशियन"},
    ],

    # 2. Skills: 7 "current" and 3 "next" skills per role with Hindi names
    "skills": [
        # --- TAILOR ---
        # Current skills (7) - includes blouse stitching, salwar suit stitching, alterations, embroidery
        {"role": "Tailor", "name": "Blouse Stitching", "name_hi": "ब्लाउज सिलाई", "level": "current"},
        {"role": "Tailor", "name": "Salwar Suit Stitching", "name_hi": "सलवार सूट सिलाई", "level": "current"},
        {"role": "Tailor", "name": "Alterations", "name_hi": "आल्टरेशन व मरम्मत", "level": "current"},
        {"role": "Tailor", "name": "Embroidery", "name_hi": "कढ़ाई कार्य", "level": "current"},
        {"role": "Tailor", "name": "Fabric Cutting & Marking", "name_hi": "कपड़े की कटाई और निशान लगाना", "level": "current"},
        {"role": "Tailor", "name": "Body Measurement & Sizing", "name_hi": "नाप लेना और साइजिंग", "level": "current"},
        {"role": "Tailor", "name": "Sewing Machine Maintenance", "name_hi": "सिलाई मशीन की मरम्मत व रखरखाव", "level": "current"},
        # Next-level skills (3)
        {"role": "Tailor", "name": "Pattern Drafting & Boutique Designing", "name_hi": "पैटर्न मेकिंग और बुटीक डिजाइनिंग", "level": "next"},
        {"role": "Tailor", "name": "Computerized Embroidery Machine Operation", "name_hi": "कंप्यूटरीकृत कढ़ाई मशीन संचालन", "level": "next"},
        {"role": "Tailor", "name": "Quality Control & Industrial Finishing", "name_hi": "औद्योगिक गारमेंट फिनिशिंग और गुणवत्ता जांच", "level": "next"},

        # --- COOK ---
        # Current skills (7)
        {"role": "Cook", "name": "Vegetable & Ingredient Prep", "name_hi": "सब्जी व खाद्य सामग्री की तैयारी", "level": "current"},
        {"role": "Cook", "name": "Regional Curry & Gravy Cooking", "name_hi": "भारतीय क्षेत्रीय करी और ग्रेवी पकाना", "level": "current"},
        {"role": "Cook", "name": "Roti, Naan & Bread Making", "name_hi": "रोटी, नान और परांठे बनाना", "level": "current"},
        {"role": "Cook", "name": "Spice Blending & Flavour Balancing", "name_hi": "मसालों का मिश्रण और स्वाद संतुलन", "level": "current"},
        {"role": "Cook", "name": "Kitchen Hygiene & Safe Storage", "name_hi": "रसोई स्वच्छता और सुरक्षित खाद्य भंडारण", "level": "current"},
        {"role": "Cook", "name": "Tandoor & Grilling", "name_hi": "तंदूर और ग्रिलिंग कार्य", "level": "current"},
        {"role": "Cook", "name": "Bulk Cooking for Events", "name_hi": "समारोहों के लिए थोक में भोजन तैयार करना", "level": "current"},
        # Next-level skills (3)
        {"role": "Cook", "name": "Commercial Food Safety & FSSAI Standards", "name_hi": "व्यावसायिक खाद्य सुरक्षा और FSSAI मानक", "level": "next"},
        {"role": "Cook", "name": "Continental & Multi-Cuisine Preparation", "name_hi": "कॉन्टिनेंटल और मल्टी-क्युज़ीन कुकिंग", "level": "next"},
        {"role": "Cook", "name": "Kitchen Costing & Inventory Management", "name_hi": "रसोई लागत और इन्वेंट्री प्रबंधन", "level": "next"},

        # --- ELECTRICIAN ---
        # Current skills (7)
        {"role": "Electrician", "name": "Domestic House Wiring & Conduits", "name_hi": "घरेलू वायरिंग और पाइपिंग फिटिंग", "level": "current"},
        {"role": "Electrician", "name": "Switchboard Assembly & Socket Installation", "name_hi": "स्विचबोर्ड संयोजन और सॉकेट फिटिंग", "level": "current"},
        {"role": "Electrician", "name": "MCB & Distribution Board Setup", "name_hi": "एमसीबी और वितरण बोर्ड लगाना", "level": "current"},
        {"role": "Electrician", "name": "Appliance Fault Diagnostics & Repair", "name_hi": "बिजली उपकरणों की खराबी पहचानना और मरम्मत", "level": "current"},
        {"role": "Electrician", "name": "Multimeter & Voltage Testing", "name_hi": "मल्टीमीटर और वोल्टेज जांच", "level": "current"},
        {"role": "Electrician", "name": "Earthing & Surge Protection", "name_hi": "अर्थिंग और सुरक्षा अर्थिंग लगाना", "level": "current"},
        {"role": "Electrician", "name": "Inverter & Battery Connection", "name_hi": "इन्वर्टर और बैटरी कनेक्शन", "level": "current"},
        # Next-level skills (3)
        {"role": "Electrician", "name": "Solar Rooftop PV Panel Installation", "name_hi": "सोलर रूफटॉप पैनल स्थापना और इन्वर्टर सिंक", "level": "next"},
        {"role": "Electrician", "name": "Industrial 3-Phase Control Panel Wiring", "name_hi": "औद्योगिक 3-फेज कंट्रोल पैनल वायरिंग", "level": "next"},
        {"role": "Electrician", "name": "Smart Home IoT Automation Wiring", "name_hi": "स्मार्ट होम आईओटी ऑटोमेशन वायरिंग", "level": "next"},
    ],

    # 3. Courses: 1 course per role, marked is_sample = 1
    "courses": [
        {
            "role": "Tailor",
            "title": "Advanced Garment Construction & Boutique Masterclass",
            "provider": "Skill India Digital (Apparel Sector Council)",
            "duration": "4 Weeks",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
        {
            "role": "Cook",
            "title": "Commercial Culinary Operations & Food Hygiene (FSSAI)",
            "provider": "Tourism & Hospitality Skill Council via Skill India",
            "duration": "3 Weeks",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
        {
            "role": "Electrician",
            "title": "Solar Rooftop Grid-Connected PV Technician",
            "provider": "Power Sector Skill Council via Skill India",
            "duration": "6 Weeks",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
    ],

    # 4. Certification Centres: 1 RPL / skill certification centre per role, marked is_sample = 1
    "centres": [
        {
            "role": "Tailor",
            "name": "Pradhan Mantri Kaushal Kendra (PMKK) - RPL Apparel Centre",
            "city": "New Delhi",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
        {
            "role": "Cook",
            "name": "National Council for Hotel Management RPL Hub",
            "city": "Mumbai",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
        {
            "role": "Electrician",
            "name": "National Skill Training Institute (NSTI) RPL Electrical Hub",
            "city": "Bengaluru",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
    ],

    # 5. Schemes: Only real official portals (myscheme.gov.in, skillindiadigital.gov.in, pmvishwakarma.gov.in), marked is_sample = 1
    "schemes": [
        {
            "key": "pm_vishwakarma",
            "name": "PM Vishwakarma Scheme",
            "name_hi": "पीएम विश्वकर्मा योजना",
            "reason": "Provides ₹15,000 modern toolkit incentive, certified skill training with ₹500/day stipend, and collateral-free enterprise loan up to ₹3 Lakhs at 5% interest.",
            "link": "https://pmvishwakarma.gov.in",
            "is_sample": 1,
        },
        {
            "key": "skill_india_rpl",
            "name": "Skill India Digital Recognition of Prior Learning (RPL)",
            "name_hi": "स्किल इंडिया डिजिटल पूर्व शिक्षण की मान्यता (RPL)",
            "reason": "Formal government assessment recognizing informal work experience with an NSQF certificate and digital skill ID.",
            "link": "https://www.skillindiadigital.gov.in",
            "is_sample": 1,
        },
        {
            "key": "pm_svanidhi",
            "name": "PM SVANidhi Scheme",
            "name_hi": "पीएम स्वनिधि योजना",
            "reason": "Collateral-free working capital loan with interest subsidy and digital cashback for informal food makers, cooks, and street vendors.",
            "link": "https://www.myscheme.gov.in",
            "is_sample": 1,
        },
        {
            "key": "pm_surya_ghar",
            "name": "PM Surya Ghar: Muft Bijli Yojana",
            "name_hi": "पीएम सूर्य घर: मुफ्त बिजली योजना",
            "reason": "Training and empanelment initiative for electricians to become certified rooftop solar panel installation vendors.",
            "link": "https://www.myscheme.gov.in",
            "is_sample": 1,
        },
    ],

    # 6. Role to Scheme associations
    "role_schemes": [
        {"role": "Tailor", "scheme_key": "pm_vishwakarma"},
        {"role": "Tailor", "scheme_key": "skill_india_rpl"},
        {"role": "Cook", "scheme_key": "pm_svanidhi"},
        {"role": "Cook", "scheme_key": "skill_india_rpl"},
        {"role": "Electrician", "scheme_key": "pm_surya_ghar"},
        {"role": "Electrician", "scheme_key": "pm_vishwakarma"},
        {"role": "Electrician", "scheme_key": "skill_india_rpl"},
    ],
}


# ==============================================================================
# SEEDING EXECUTION (Generic loops, never changes when data is updated)
# ==============================================================================

def seed():
    """Initializes schema and refills sample data without touching skill_cards."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear previous sample data (Foreign key order, NEVER delete skill_cards)
    cursor.execute("DELETE FROM role_schemes;")
    cursor.execute("DELETE FROM schemes;")
    cursor.execute("DELETE FROM centres;")
    cursor.execute("DELETE FROM courses;")
    cursor.execute("DELETE FROM skills;")
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('skills', 'courses', 'centres', 'schemes');")
    except sqlite3.OperationalError:
        pass

    # 1. Upsert Job Roles (Preserves IDs so existing skill_cards referencing job_roles never violate FK)
    role_id_map = {}
    for r in SEED_DATA["job_roles"]:
        cursor.execute("SELECT id FROM job_roles WHERE name = ?;", (r["name"],))
        row = cursor.fetchone()
        if row:
            role_id = row["id"]
            cursor.execute("UPDATE job_roles SET name_hi = ? WHERE id = ?;", (r["name_hi"], role_id))
        else:
            cursor.execute(
                "INSERT INTO job_roles (name, name_hi) VALUES (?, ?);",
                (r["name"], r["name_hi"]),
            )
            role_id = cursor.lastrowid
        role_id_map[r["name"]] = role_id

    # 2. Insert Skills
    for s in SEED_DATA["skills"]:
        cursor.execute(
            """
            INSERT INTO skills (role_id, name, name_hi, level)
            VALUES (?, ?, ?, ?);
            """,
            (role_id_map[s["role"]], s["name"], s["name_hi"], s["level"]),
        )

    # 3. Insert Courses
    for c in SEED_DATA["courses"]:
        cursor.execute(
            """
            INSERT INTO courses (role_id, title, provider, duration, link, is_sample)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (role_id_map[c["role"]], c["title"], c["provider"], c["duration"], c["link"], c["is_sample"]),
        )

    # 4. Insert Centres
    for cnt in SEED_DATA["centres"]:
        cursor.execute(
            """
            INSERT INTO centres (role_id, name, city, link, is_sample)
            VALUES (?, ?, ?, ?, ?);
            """,
            (role_id_map[cnt["role"]], cnt["name"], cnt["city"], cnt["link"], cnt["is_sample"]),
        )

    # 5. Insert Schemes
    scheme_id_map = {}
    for sch in SEED_DATA["schemes"]:
        cursor.execute(
            """
            INSERT INTO schemes (name, name_hi, reason, link, is_sample)
            VALUES (?, ?, ?, ?, ?);
            """,
            (sch["name"], sch["name_hi"], sch["reason"], sch["link"], sch["is_sample"]),
        )
        scheme_id_map[sch["key"]] = cursor.lastrowid

    # 6. Insert Role-Scheme Associations
    for rs in SEED_DATA["role_schemes"]:
        cursor.execute(
            """
            INSERT INTO role_schemes (role_id, scheme_id)
            VALUES (?, ?);
            """,
            (role_id_map[rs["role"]], scheme_id_map[rs["scheme_key"]]),
        )

    conn.commit()

    # Query counts for verification
    counts = {}
    for table in ["job_roles", "skills", "courses", "centres", "schemes", "role_schemes", "skill_cards"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        counts[table] = cursor.fetchone()[0]

    conn.close()

    print("========================================")
    print("Database Seeded Successfully!")
    for table, count in counts.items():
        print(f"  - {table:<15}: {count} rows")
    print("========================================")
    return counts


if __name__ == "__main__":
    seed()
