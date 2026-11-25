// SkillCard.js - Screen 4
// Features: Worker name, job role, skills as chips, years of experience, QR code,
// disclaimer note, buttons (Share on WhatsApp, Download card, See your path).

window.SkillCard = function SkillCard({ t, lang, workerData, onSeePath }) {
  const [downloadSuccess, setDownloadSuccess] = React.useState(false);

  const cardId = workerData.card_id || "hs-" + Math.random().toString(36).substring(2, 8);
  const yearsText = t.experienceYears.replace("{years}", workerData.years_experience || 8);
  const publicUrl = workerData.public_card_url || `https://honorary.stats/verify/${cardId}`;

  // Use backend-provided WhatsApp link or construct a robust fallback
  let whatsappUrl = workerData.whatsapp_url;
  if (!whatsappUrl) {
    const shareText = encodeURIComponent(
      `*honorary.stats Skill Card*\n` +
      `Name: ${workerData.name}\n` +
      `Role: ${workerData.role}\n` +
      `Experience: ${workerData.years_experience} years\n` +
      `Skills: ${(workerData.skills || []).join(", ")}\n` +
      `Verify: ${publicUrl}`
    );
    whatsappUrl = `https://wa.me/?text=${shareText}`;
  }

  const handleDownload = () => {
    if (workerData.download_url) {
      window.location.href = workerData.download_url;
    } else {
      setDownloadSuccess(true);
      setTimeout(() => {
        window.print();
      }, 200);
      setTimeout(() => {
        setDownloadSuccess(false);
      }, 4000);
    }
  };

  const qrTitle = lang === "kn" 
    ? "ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ಕೌಶಲ್ಯ ಪರಿಶೀಲಿಸಿ" 
    : (lang === "hi" ? "स्कैन कर हुनर जांचें" : "Scan to verify skills");

  const qrDesc = lang === "kn"
    ? "ಯಾವುದೇ ಗ್ರಾಹಕರು ಅಥವಾ ಗುತ್ತಿಗೆದಾರರು ಈ ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ನಿಮ್ಮ ವಿವರಗಳನ್ನು ನೋಡಬಹುದು."
    : (lang === "hi" 
        ? "कोई भी ग्राहक या ठेकेदार यह कोड स्कैन करके आपका प्रोफाइल देख सकता है।"
        : "Clients and employers can scan to view your verified details instantly.");

  const successNotice = lang === "kn"
    ? "✓ ಕಾರ್ಡ್ ಪ್ರಿಂಟ್ / ಸೇವ್ ಮಾಡಲು ಸಿದ್ಧವಾಗಿದೆ!"
    : (lang === "hi" ? "✓ कार्ड प्रिंट / सेव करने के लिए तैयार है!" : "✓ Card ready for print or PDF save!");

  return (
    <div className="main-content">
      <div style={{ textAlign: "center", marginBottom: "var(--space-md)" }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", marginBottom: "var(--space-xs)" }}>
          {t.cardHeading}
        </h2>
        <p className="subheading" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-sm)" }}>
          {t.cardSubheading}
        </p>
      </div>

      {/* Visual Skill Card Container */}
      <div className="id-card-visual" id="printable-skill-card">
        <div className="id-card-header">
          <div>
            <div style={{ fontSize: "0.813rem", fontWeight: "700", color: "var(--text-muted)", letterSpacing: "0.5px" }}>
              HONORARY.STATS SKILL CARD
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-light)" }}>
              ID: {cardId}
            </div>
          </div>
          <span className="id-card-badge">
            ✓ {t.verifiedBadge}
          </span>
        </div>

        <div className="id-card-body">
          <div className="worker-name">{workerData.name}</div>
          <div className="worker-role-exp">
            {workerData.role} • {yearsText}
          </div>

          <div style={{ fontSize: "0.875rem", fontWeight: "700", color: "var(--text-charcoal)", marginBottom: "6px" }}>
            {t.skillsHeadline}:
          </div>
          <div className="chips-container" style={{ marginTop: 0 }}>
            {(workerData.skills || []).map((skill, index) => (
              <span key={index} className="chip">
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* QR Code and Quick Info */}
        <div className="id-card-qr-box">
          <div className="qr-code-graphic" title="Skill verification QR">
            {/* Live QR Image from backend, or offline SVG fallback */}
            {workerData.qr_data_uri ? (
              <img
                src={workerData.qr_data_uri}
                alt="Verification QR Code"
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
              />
            ) : (
              <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <rect width="100" height="100" fill="#FFFFFF"/>
                <rect x="10" y="10" width="28" height="28" fill="#26292B"/>
                <rect x="15" y="15" width="18" height="18" fill="#FFFFFF"/>
                <rect x="20" y="20" width="8" height="8" fill="#26292B"/>
                <rect x="62" y="10" width="28" height="28" fill="#26292B"/>
                <rect x="67" y="15" width="18" height="18" fill="#FFFFFF"/>
                <rect x="72" y="20" width="8" height="8" fill="#26292B"/>
                <rect x="10" y="62" width="28" height="28" fill="#26292B"/>
                <rect x="15" y="67" width="18" height="18" fill="#FFFFFF"/>
                <rect x="20" y="72" width="8" height="8" fill="#26292B"/>
                <rect x="46" y="14" width="8" height="8" fill="#C36145"/>
                <rect x="46" y="28" width="8" height="8" fill="#5E8A68"/>
                <rect x="14" y="46" width="8" height="8" fill="#26292B"/>
                <rect x="28" y="46" width="8" height="8" fill="#4E7699"/>
                <rect x="46" y="46" width="12" height="12" fill="#26292B"/>
                <rect x="66" y="46" width="8" height="8" fill="#26292B"/>
                <rect x="80" y="46" width="8" height="8" fill="#C36145"/>
                <rect x="46" y="66" width="8" height="8" fill="#5E8A68"/>
                <rect x="66" y="66" width="12" height="12" fill="#26292B"/>
                <rect x="82" y="82" width="8" height="8" fill="#4E7699"/>
              </svg>
            )}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.875rem", fontWeight: "700", color: "var(--text-charcoal)" }}>
              {qrTitle}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
              {qrDesc}
            </div>
          </div>
        </div>

        {/* Required Disclaimer */}
        <div className="id-card-disclaimer">
          {t.cardDisclaimer}
        </div>
      </div>

      {/* Generated Image Preview Link if available */}
      {workerData.image_url && (
        <div style={{ textAlign: "center", marginBottom: "var(--space-md)" }}>
          <a
            href={workerData.image_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-link"
            style={{ fontSize: "0.875rem", fontWeight: "700" }}
          >
            🖼️ {lang === "kn" ? "ಪೂರ್ಣ ಕಾರ್ಡ್ ಚಿತ್ರವನ್ನು ವೀಕ್ಷಿಸಿ (PNG)" : (lang === "hi" ? "पूरा कार्ड चित्र देखें (PNG)" : "View full generated card PNG")} →
          </a>
        </div>
      )}

      {downloadSuccess && (
        <div className="card" style={{ background: "var(--accent-sage-bg)", borderColor: "var(--accent-sage-border)", marginBottom: "var(--space-md)", textAlign: "center", padding: "12px" }}>
          <p style={{ color: "var(--accent-sage)", fontWeight: "700", fontSize: "0.938rem" }}>
            {successNotice}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="stack" style={{ gap: "var(--space-sm)" }}>
        {/* 1. Share on WhatsApp */}
        <a
          href={whatsappUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn"
          style={{ background: "#25D366", color: "#FFFFFF", textDecoration: "none" }}
        >
          <span>💬</span>
          <span>{t.shareWhatsAppBtn}</span>
        </a>

        {/* 2. Download Card */}
        <button
          type="button"
          className="btn btn-outline"
          onClick={handleDownload}
        >
          <span>📥</span>
          <span>{t.downloadCardBtn}</span>
        </button>

        {/* 3. See your path */}
        <button
          type="button"
          className="btn btn-terracotta"
          onClick={onSeePath}
          style={{ marginTop: "var(--space-xs)" }}
        >
          <span>🧭</span>
          <span>{t.seePathBtn}</span>
          <span>→</span>
        </button>
      </div>
    </div>
  );
};
