// Path.js - Screen 5
// Features: Four cards (Skill gap, Next course, Nearest centre, Schemes),
// Under Schemes: "Sample data - verify before applying",
// Listen button on each card (plays ElevenLabs audio via /api/voice with clean stop/revoke,
// and graceful fallback to browser speechSynthesis),
// View Card Again / Start Fresh options.

window.Path = function Path({ t, lang, pathData, onViewCard, onStartFresh }) {
  const [speakingCard, setSpeakingCard] = React.useState(null);
  const currentAudioRef = React.useRef(null);
  const currentAudioUrlRef = React.useRef(null);

  // Four Cards Data (supports en, hi, kn)
  const course = pathData.next_course || {};
  const centre = pathData.nearest_centre || {};
  const schemes = pathData.schemes || [];
  
  // Localized skill gaps
  const skillGaps = (lang !== "en" && pathData["skill_gap_" + lang]) 
    ? pathData["skill_gap_" + lang] 
    : (pathData.skill_gap || []);

  const getCourseTitle = () => {
    if (lang === "kn" && course.title_kn) return course.title_kn;
    if (lang === "hi" && course.title_hi) return course.title_hi;
    return course.title;
  };

  const getCourseDuration = () => {
    if (lang === "kn" && course.duration_kn) return course.duration_kn;
    if (lang === "hi" && course.duration_hi) return course.duration_hi;
    return course.duration;
  };

  const getCentreCity = () => {
    if (lang === "kn" && centre.city_kn) return centre.city_kn;
    if (lang === "hi" && centre.city_hi) return centre.city_hi;
    return centre.city;
  };

  const getSchemeName = (s) => {
    if (lang === "kn" && s.name_kn) return s.name_kn;
    if (lang === "hi" && s.name_hi) return s.name_hi;
    return s.name;
  };

  const getSchemeReason = (s) => {
    if (lang === "kn" && s.reason_kn) return s.reason_kn;
    if (lang === "hi" && s.reason_hi) return s.reason_hi;
    return s.reason;
  };

  // Clean stop and cleanup of any currently playing audio
  const stopCurrentAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    if (currentAudioUrlRef.current) {
      URL.revokeObjectURL(currentAudioUrlRef.current);
      currentAudioUrlRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  };

  React.useEffect(() => {
    return () => {
      stopCurrentAudio();
    };
  }, []);

  const handleListen = (cardId, textToRead) => {
    // If tapping the already playing card, stop it
    if (speakingCard === cardId) {
      stopCurrentAudio();
      setSpeakingCard(null);
      return;
    }

    stopCurrentAudio();
    setSpeakingCard(cardId);

    // Browser SpeechSynthesis fallback
    const playFallbackSpeech = () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(textToRead);
        utterance.lang = lang === "kn" ? "kn-IN" : (lang === "hi" ? "hi-IN" : "en-IN");
        utterance.rate = 0.95;
        utterance.onend = () => setSpeakingCard(null);
        utterance.onerror = () => setSpeakingCard(null);
        window.speechSynthesis.speak(utterance);
      } else {
        setTimeout(() => setSpeakingCard(null), 3500);
      }
    };

    // Attempt streaming from backend /api/voice
    fetch("/api/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: textToRead, language: lang })
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Voice API returned status ${res.status}`);
        }
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        currentAudioUrlRef.current = audioUrl;

        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;

        audio.onended = () => {
          setSpeakingCard(null);
          if (currentAudioUrlRef.current) {
            URL.revokeObjectURL(currentAudioUrlRef.current);
            currentAudioUrlRef.current = null;
          }
          currentAudioRef.current = null;
        };

        audio.onerror = () => {
          playFallbackSpeech();
        };

        audio.play().catch(() => {
          playFallbackSpeech();
        });
      })
      .catch((err) => {
        console.log("Using browser speech synthesis fallback:", err.message);
        playFallbackSpeech();
      });
  };

  const courseLinkText = lang === "kn" ? "ಕೋರ್ಸ್ ಮಾಹಿತಿ ನೋಡಿ →" : (lang === "hi" ? "कोर्स की जानकारी देखें →" : "View course details →");
  const centreLinkText = lang === "kn" ? "ಕೇಂದ್ರದ ವಿಳಾಸ ಮತ್ತು ಸಂಪರ್ಕ →" : (lang === "hi" ? "कौशल केंद्र का पता और संपर्क →" : "Get directions & centre info →");
  const portalLinkText = lang === "kn" ? "ಪೋರ್ಟಲ್ ಲಿಂಕ್ →" : (lang === "hi" ? "पोर्टल खोलें →" : "Apply / Portal link →");
  const summaryHeading = lang === "kn" ? "ಹಾದಿಯ ಸಾರಾಂಶ" : (lang === "hi" ? "मार्ग का सारांश" : "Path Summary");

  return (
    <div className="main-content">
      <div style={{ textAlign: "center", marginBottom: "var(--space-md)" }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", marginBottom: "var(--space-xs)" }}>
          {t.pathHeading}
        </h2>
        <p className="subheading" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-md)" }}>
          {t.pathSubheading}
        </p>
      </div>

      <div className="path-cards-list">
        {/* CARD 1: Skill Gap */}
        <div className="path-card">
          <div className="path-card-header">
            <div className="path-card-title-group">
              <div className="path-card-icon icon-gap">🎯</div>
              <h3 style={{ fontSize: "1.1rem" }}>{t.skillGapTitle}</h3>
            </div>
            <button
              type="button"
              className={`btn-listen ${speakingCard === "gap" ? "speaking" : ""}`}
              onClick={() => handleListen(
                "gap",
                `${t.skillGapTitle}: ${skillGaps.join(", ")}`
              )}
            >
              <span>{speakingCard === "gap" ? "🔊" : "🔈"}</span>
              <span>{speakingCard === "gap" ? t.listeningState : t.listenBtn}</span>
            </button>
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "8px" }}>
            {t.skillGapDesc}
          </p>
          <div className="chips-container" style={{ marginTop: 0 }}>
            {skillGaps.map((gap, idx) => (
              <span key={idx} className="chip chip-terracotta">
                + {gap}
              </span>
            ))}
          </div>
        </div>

        {/* CARD 2: Next Course */}
        <div className="path-card">
          <div className="path-card-header">
            <div className="path-card-title-group">
              <div className="path-card-icon icon-course">📚</div>
              <h3 style={{ fontSize: "1.1rem" }}>{t.nextCourseTitle}</h3>
            </div>
            <button
              type="button"
              className={`btn-listen ${speakingCard === "course" ? "speaking" : ""}`}
              onClick={() => handleListen(
                "course",
                `${t.nextCourseTitle}: ${getCourseTitle()}. ${course.provider}. ${getCourseDuration()}`
              )}
            >
              <span>{speakingCard === "course" ? "🔊" : "🔈"}</span>
              <span>{speakingCard === "course" ? t.listeningState : t.listenBtn}</span>
            </button>
          </div>

          <div style={{ marginTop: "4px" }}>
            <h4 style={{ fontSize: "1rem", color: "var(--accent-blue)", marginBottom: "4px" }}>
              {getCourseTitle()}
            </h4>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
              🏛️ {course.provider}
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-charcoal)", fontWeight: "600", marginTop: "2px" }}>
              ⏱️ {getCourseDuration()}
            </div>

            {course.link && (
              <a
                href={course.link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-link"
                style={{ display: "inline-block", marginTop: "8px", fontSize: "0.875rem" }}
              >
                {courseLinkText}
              </a>
            )}
          </div>
        </div>

        {/* CARD 3: Nearest Centre */}
        <div className="path-card">
          <div className="path-card-header">
            <div className="path-card-title-group">
              <div className="path-card-icon icon-centre">📍</div>
              <h3 style={{ fontSize: "1.1rem" }}>{t.nearestCentreTitle}</h3>
            </div>
            <button
              type="button"
              className={`btn-listen ${speakingCard === "centre" ? "speaking" : ""}`}
              onClick={() => handleListen(
                "centre",
                `${t.nearestCentreTitle}: ${centre.name}, ${getCentreCity()}`
              )}
            >
              <span>{speakingCard === "centre" ? "🔊" : "🔈"}</span>
              <span>{speakingCard === "centre" ? t.listeningState : t.listenBtn}</span>
            </button>
          </div>

          <div style={{ marginTop: "4px" }}>
            <h4 style={{ fontSize: "1rem", color: "var(--text-charcoal)", marginBottom: "2px" }}>
              {centre.name}
            </h4>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
              📌 {getCentreCity()}
            </div>

            {centre.link && (
              <a
                href={centre.link}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-link"
                style={{ display: "inline-block", marginTop: "8px", fontSize: "0.875rem" }}
              >
                {centreLinkText}
              </a>
            )}
          </div>
        </div>

        {/* CARD 4: Schemes */}
        <div className="path-card">
          <div className="path-card-header">
            <div className="path-card-title-group">
              <div className="path-card-icon icon-schemes">🏛️</div>
              <h3 style={{ fontSize: "1.1rem" }}>{t.schemesTitle}</h3>
            </div>
            <button
              type="button"
              className={`btn-listen ${speakingCard === "schemes" ? "speaking" : ""}`}
              onClick={() => handleListen(
                "schemes",
                `${t.schemesTitle}: ` + schemes.map(s => getSchemeName(s)).join(". ")
              )}
            >
              <span>{speakingCard === "schemes" ? "🔊" : "🔈"}</span>
              <span>{speakingCard === "schemes" ? t.listeningState : t.listenBtn}</span>
            </button>
          </div>

          <div style={{ marginTop: "4px" }}>
            {schemes.map((scheme, idx) => (
              <div key={idx} className="scheme-item">
                <div className="scheme-name">
                  {getSchemeName(scheme)}
                </div>
                <div className="scheme-reason">
                  {getSchemeReason(scheme)}
                </div>
                {scheme.link && (
                  <a
                    href={scheme.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-link"
                    style={{ fontSize: "0.813rem", marginTop: "4px", display: "inline-block" }}
                  >
                    {portalLinkText}
                  </a>
                )}
              </div>
            ))}

            {/* Required Disclaimer */}
            <div className="scheme-disclaimer">
              ℹ️ {t.schemesDisclaimer}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Box */}
      {pathData.summary && (
        <div className="card" style={{ marginTop: "var(--space-md)", background: "var(--bg-subtle)" }}>
          <div style={{ fontSize: "0.813rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
            {summaryHeading}
          </div>
          <p style={{ fontSize: "0.938rem", color: "var(--text-charcoal)", marginTop: "4px", lineHeight: "1.5" }}>
            {pathData.summary}
          </p>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="stack" style={{ marginTop: "var(--space-lg)", gap: "var(--space-sm)" }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onViewCard}
        >
          <span>←</span>
          <span>{t.viewCardAgainBtn}</span>
        </button>

        <button
          type="button"
          className="btn btn-outline"
          onClick={onStartFresh}
        >
          <span>🔄</span>
          <span>{t.startFreshBtn}</span>
        </button>
      </div>
    </div>
  );
};
