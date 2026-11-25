// App.js - Main Application Orchestrator for honorary.stats
// Supported Languages: English ('en'), Hindi ('hi'), Kannada ('kn')

const { useState, useEffect } = React;

function App() {
  const [step, setStep] = useState(1); // 1: Welcome, 2: Speak, 3: Confirm, 4: SkillCard, 5: Path
  const [lang, setLang] = useState("hi"); // Default to Hindi, toggles between en, hi, kn
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [initialSpeakMode, setInitialSpeakMode] = useState("mic");

  // Helper to extract localized persona data
  const getPersonaData = (persona, targetLang) => {
    const isEn = targetLang === "en";
    const name = (!isEn && persona["name_" + targetLang]) ? persona["name_" + targetLang] : persona.name;
    const role = (!isEn && persona["role_" + targetLang]) ? persona["role_" + targetLang] : persona.role;
    const skills = (!isEn && persona["skills_" + targetLang]) ? persona["skills_" + targetLang] : persona.skills;
    const transcript = (!isEn && persona["transcript_" + targetLang]) ? persona["transcript_" + targetLang] : persona.transcript_en;
    return { name, role, skills, transcript };
  };

  // Initial Worker Profile State (Tailor Sunita)
  const defaultTailor = window.samplePersonas?.tailor || {};
  const [workerData, setWorkerData] = useState(() => {
    const loc = getPersonaData(defaultTailor, "hi");
    return {
      name: loc.name,
      role: loc.role,
      skills: [...loc.skills],
      years_experience: 8,
      card_id: "hs-tailor-8821",
      language: "hi",
      personaKey: "tailor",
      image_url: null,
      download_url: null,
      qr_data_uri: null,
      public_card_url: null,
      whatsapp_url: null
    };
  });

  // Path Recommendations State
  const [pathData, setPathData] = useState(defaultTailor.path || {});

  // Dictionary translations
  const t = (window.translations && window.translations[lang]) ? window.translations[lang] : window.translations["en"];

  // Update browser tab title
  useEffect(() => {
    document.title = "honorary.stats";
  }, []);

  // Back Navigation handler
  const handleBack = () => {
    setErrorMessage("");
    if (step > 1) {
      setStep(step - 1);
    }
  };

  // Language Toggle (en / hi / kn)
  const toggleLanguage = (newLang) => {
    setLang(newLang);
    const currentPersona = window.samplePersonas?.[workerData.personaKey || "tailor"];
    if (currentPersona) {
      const loc = getPersonaData(currentPersona, newLang);
      setWorkerData(prev => ({
        ...prev,
        name: loc.name,
        role: loc.role,
        skills: [...loc.skills],
        language: newLang
      }));
    }
  };

  // DEMO MODE: Run complete flow automatically with selected persona
  const handleRunDemo = (personaKey = "tailor") => {
    const persona = window.samplePersonas?.[personaKey] || window.samplePersonas?.tailor;
    if (!persona) return;

    setIsLoading(true);
    setErrorMessage("");

    const preferredLang = persona.preferred_language || lang;
    setLang(preferredLang);

    const loc = getPersonaData(persona, preferredLang);

    setWorkerData({
      name: loc.name,
      role: loc.role,
      skills: [...loc.skills],
      years_experience: persona.years_experience,
      card_id: "hs-" + personaKey + "-" + Math.floor(1000 + Math.random() * 9000),
      language: preferredLang,
      transcript: loc.transcript,
      personaKey: personaKey,
      image_url: null,
      download_url: null,
      qr_data_uri: null,
      public_card_url: null,
      whatsapp_url: null
    });

    setPathData(persona.path);

    setTimeout(() => {
      setIsLoading(false);
      setStep(3); // Go straight to Confirm screen
    }, 450);
  };

  // STEP 2 -> STEP 3: Voice / Text Analysis (POST /api/analyze with fallback)
  const handleSpeakContinue = async (inputText) => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText, language: lang })
      });

      if (response.ok) {
        const data = await response.json();
        setWorkerData(prev => ({
          ...prev,
          role: data.role || prev.role,
          skills: data.skills && data.skills.length > 0 ? data.skills : prev.skills,
          years_experience: data.years_experience !== null ? data.years_experience : prev.years_experience,
          transcript: data.transcript || inputText
        }));
        setIsLoading(false);
        setStep(3);
        return;
      }
    } catch (err) {
      console.log("Using safe client-side fallback analysis");
    }

    // Keyword matching supporting English, Hindi, and Kannada
    const lower = inputText.toLowerCase();
    let detectedPersonaKey = "tailor";

    if (
      lower.includes("cook") || lower.includes("खाना") || lower.includes("रसोई") ||
      lower.includes("ಅಡುಗೆ") || lower.includes("curry") || lower.includes("catering")
    ) {
      detectedPersonaKey = "cook";
    } else if (
      lower.includes("electric") || lower.includes("बिजली") || lower.includes("wire") ||
      lower.includes("ವಿದ್ಯುತ್") || lower.includes("ವೈರಿಂಗ್") || lower.includes("inverter")
    ) {
      detectedPersonaKey = "electrician";
    }

    const detectedPersona = window.samplePersonas[detectedPersonaKey];
    const loc = getPersonaData(detectedPersona, lang);

    setWorkerData({
      name: loc.name,
      role: loc.role,
      skills: [...loc.skills],
      years_experience: detectedPersona.years_experience,
      card_id: "hs-" + Math.floor(1000 + Math.random() * 9000),
      language: lang,
      transcript: inputText,
      personaKey: detectedPersonaKey,
      image_url: null,
      download_url: null,
      qr_data_uri: null,
      public_card_url: null,
      whatsapp_url: null
    });
    setPathData(detectedPersona.path);

    setTimeout(() => {
      setIsLoading(false);
      setStep(3);
    }, 400);
  };

  // STEP 3 -> STEP 4: Confirm Card (POST /api/card with async bug fix & asset clearing)
  const handleConfirmSkills = async (confirmedData) => {
    setIsLoading(true);
    setErrorMessage("");

    // Merge directly from confirmedData to eliminate async state lag
    const confirmedWorker = {
      ...workerData,
      ...(confirmedData || {}),
      language: lang,
      // Clear stale asset fields before fetching
      image_url: null,
      download_url: null,
      qr_data_uri: null,
      public_card_url: null,
      whatsapp_url: null
    };

    try {
      const response = await fetch("/api/card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: confirmedWorker.name,
          role: confirmedWorker.role,
          skills: confirmedWorker.skills,
          years_experience: confirmedWorker.years_experience,
          language: confirmedWorker.language
        })
      });

      if (response.ok) {
        const data = await response.json();
        setWorkerData(prev => ({
          ...prev,
          ...confirmedWorker,
          card_id: data.card_id || prev.card_id,
          image_url: data.image_url || null,
          download_url: data.download_url || null,
          qr_data_uri: data.qr_data_uri || null,
          public_card_url: data.public_card_url || null,
          whatsapp_url: data.whatsapp_url || null
        }));
        setIsLoading(false);
        setStep(4);
        return;
      }
    } catch (err) {
      console.log("Using safe client-side fallback card creation:", err);
    }

    setWorkerData(prev => ({
      ...prev,
      ...confirmedWorker
    }));
    setTimeout(() => {
      setIsLoading(false);
      setStep(4);
    }, 350);
  };

  // STEP 4 -> STEP 5: See Path (GET /api/path/{id} with fallback)
  const handleSeePath = async () => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(`/api/path/${workerData.card_id}`);
      if (response.ok) {
        const data = await response.json();
        setPathData(data);
        setIsLoading(false);
        setStep(5);
        return;
      }
    } catch (err) {
      console.log("Using safe client-side fallback path data");
    }

    setTimeout(() => {
      setIsLoading(false);
      setStep(5);
    }, 300);
  };

  // Progress Bar Step Labels
  const stepLabels = [
    t.stepWelcome,
    t.stepSpeak,
    t.stepConfirm,
    t.stepCard,
    t.stepPath
  ];

  return (
    <div className="app-container">
      {/* Global Header */}
      <header className="app-header">
        <div
          className="logo-container"
          onClick={() => setStep(1)}
          title="Go to home screen"
        >
          <span className="logo-text">
            honorary<span className="logo-dot">.</span>stats
          </span>
        </div>

        <div className="header-controls">
          {/* Trilingual Language Toggle (English / हिंदी / ಕನ್ನಡ) */}
          <div className="lang-toggle" role="group" aria-label="Language selector">
            <button
              type="button"
              className={`lang-btn ${lang === "en" ? "active" : ""}`}
              onClick={() => toggleLanguage("en")}
            >
              English
            </button>
            <button
              type="button"
              className={`lang-btn ${lang === "hi" ? "active" : ""}`}
              onClick={() => toggleLanguage("hi")}
            >
              हिंदी
            </button>
            <button
              type="button"
              className={`lang-btn ${lang === "kn" ? "active" : ""}`}
              onClick={() => toggleLanguage("kn")}
            >
              ಕನ್ನಡ
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Bar (Back Button + 5-Step Progress Indicator) */}
      <nav className="nav-bar">
        {step > 1 ? (
          <button
            type="button"
            className="btn-back"
            onClick={handleBack}
            aria-label={t.backBtn}
            title={t.backBtn}
          >
            ←
          </button>
        ) : (
          <div style={{ width: 40, height: 40 }} />
        )}

        <div className="progress-container">
          <div className="progress-steps">
            {[1, 2, 3, 4, 5].map((s) => (
              <div
                key={s}
                className={`progress-step-pill ${
                  s < step ? "completed" : s === step ? "active" : ""
                }`}
              />
            ))}
          </div>
          <div className="progress-label">
            <span>{stepLabels[step - 1]}</span>
            <span>{t.stepCounter.replace("{current}", step)}</span>
          </div>
        </div>
      </nav>

      {/* Active Screen View */}
      {step === 1 && (
        <window.Welcome
          t={t}
          lang={lang}
          onStartSpeak={() => {
            setInitialSpeakMode("mic");
            setStep(2);
          }}
          onTypeInstead={() => {
            setInitialSpeakMode("type");
            setStep(2);
          }}
          onRunDemo={handleRunDemo}
        />
      )}

      {step === 2 && (
        <window.Speak
          t={t}
          lang={lang}
          initialText={workerData.transcript || ""}
          initialMode={initialSpeakMode}
          onContinue={handleSpeakContinue}
          isLoading={isLoading}
          errorMessage={errorMessage}
        />
      )}

      {step === 3 && (
        <window.Confirm
          t={t}
          lang={lang}
          workerData={workerData}
          onUpdateWorker={(updated) => setWorkerData(prev => ({ ...prev, ...updated }))}
          onConfirm={handleConfirmSkills}
          isLoading={isLoading}
        />
      )}

      {step === 4 && (
        <window.SkillCard
          t={t}
          lang={lang}
          workerData={workerData}
          onSeePath={handleSeePath}
        />
      )}

      {step === 5 && (
        <window.Path
          t={t}
          lang={lang}
          pathData={pathData}
          onViewCard={() => setStep(4)}
          onStartFresh={() => setStep(1)}
        />
      )}

      {/* Unified Global Footer */}
      <footer className="app-footer">
        <p className="footer-text">
          🌱 {t.footerText}
        </p>
      </footer>
    </div>
  );
}

// Render React App
const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}
