// Confirm.js - Screen 3
// Features: Detected role, skills as tappable chips (tap to remove), "add a skill" input,
// years of experience stepper, "This is right" button, loading state.

window.Confirm = function Confirm({ t, lang, workerData, onUpdateWorker, onConfirm, isLoading }) {
  const [role, setRole] = React.useState(workerData.role || "Tailor");
  const [skills, setSkills] = React.useState(workerData.skills || []);
  const [newSkillText, setNewSkillText] = React.useState("");
  const [experience, setExperience] = React.useState(Number(workerData.years_experience) || 5);
  const [name, setName] = React.useState(workerData.name || (lang === "kn" ? "ಸುನೀತಾ ದೇವಿ" : (lang === "hi" ? "सुनीता देवी" : "Sunita Devi")));

  // Synchronize if workerData changes (e.g. language toggle)
  React.useEffect(() => {
    if (workerData.name) setName(workerData.name);
    if (workerData.role) setRole(workerData.role);
    if (workerData.skills) setSkills(workerData.skills);
    if (workerData.years_experience) setExperience(Number(workerData.years_experience));
  }, [workerData]);

  const removeSkill = (indexToRemove) => {
    const updated = skills.filter((_, idx) => idx !== indexToRemove);
    setSkills(updated);
  };

  const addSkill = (e) => {
    if (e) e.preventDefault();
    const trimmed = newSkillText.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
      setNewSkillText("");
    }
  };

  const handleConfirm = () => {
    const confirmedData = {
      name,
      role,
      skills,
      years_experience: experience
    };
    onUpdateWorker(confirmedData);
    // Fix async state bug by passing confirmedData directly into onConfirm
    onConfirm(confirmedData);
  };

  const nameLabel = lang === "kn" ? "ನಿಮ್ಮ ಹೆಸರು:" : (lang === "hi" ? "आपका नाम:" : "Your name:");
  const emptySkillWarning = lang === "kn" ? "ಕನಿಷ್ಠ ಒಂದು ಕೌಶಲ್ಯವನ್ನು ಸೇರಿಸಿ." : (lang === "hi" ? "कम से कम एक हुनर जोड़ें।" : "Please add at least one skill.");
  const expUnit = lang === "kn" ? "ವರ್ಷ" : (lang === "hi" ? "साल" : "yrs");

  return (
    <div className="main-content">
      <div className="card" style={{ marginBottom: "var(--space-md)" }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", marginBottom: "var(--space-xs)" }}>
          {t.confirmHeading}
        </h2>
        <p className="subheading" style={{ fontSize: "var(--font-size-sm)", marginBottom: "var(--space-md)" }}>
          {t.confirmSubheading}
        </p>

        {/* Worker Name Input */}
        <div className="form-group">
          <label className="form-label" htmlFor="worker-name-input">
            {nameLabel}
          </label>
          <input
            id="worker-name-input"
            type="text"
            className="input-text"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        {/* Detected Role */}
        <div className="form-group">
          <label className="form-label" htmlFor="worker-role-input">
            {t.roleLabel}
          </label>
          <input
            id="worker-role-input"
            type="text"
            className="input-text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
        </div>

        {/* Skills Chips (Tap to Remove) */}
        <div className="form-group">
          <label className="form-label">
            {t.skillsDetectedLabel}
          </label>
          <div className="chips-container">
            {skills.map((skill, index) => (
              <span
                key={index}
                className="chip"
                onClick={() => removeSkill(index)}
                title={lang === "kn" ? "ತೆಗೆಯಲು ಟ್ಯಾಪ್ ಮಾಡಿ" : (lang === "hi" ? "हटाने के लिए टैप करें" : "Tap to remove")}
                role="button"
                tabIndex={0}
              >
                <span>{skill}</span>
                <span className="chip-remove">✕</span>
              </span>
            ))}
          </div>
          {skills.length === 0 && (
            <p style={{ fontSize: "0.875rem", color: "var(--accent-terracotta)", marginTop: "6px" }}>
              {emptySkillWarning}
            </p>
          )}
        </div>

        {/* Add Skill Input */}
        <form onSubmit={addSkill} className="form-group">
          <label className="form-label" htmlFor="add-skill-input">
            {t.addSkillLabel}
          </label>
          <div style={{ display: "flex", gap: "var(--space-sm)" }}>
            <input
              id="add-skill-input"
              type="text"
              className="input-text"
              placeholder={t.addSkillPlaceholder}
              value={newSkillText}
              onChange={(e) => setNewSkillText(e.target.value)}
            />
            <button
              type="button"
              className="btn btn-secondary"
              style={{ width: "auto", minWidth: "90px", padding: "0 18px" }}
              onClick={addSkill}
            >
              {t.addBtn}
            </button>
          </div>
        </form>

        {/* Years of Experience Stepper */}
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">
            {t.expLabel}
          </label>
          <div className="stepper-container">
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setExperience(Math.max(1, experience - 1))}
              aria-label="Decrease years"
            >
              −
            </button>
            <span className="stepper-value">
              {experience} {expUnit}
            </span>
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setExperience(experience + 1)}
              aria-label="Increase years"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Primary Action Button or Loading Spinner */}
      {isLoading ? (
        <div className="spinner-container">
          <div className="spinner"></div>
          <p style={{ fontWeight: "600", color: "var(--accent-sage)" }}>
            {t.savingCard}
          </p>
        </div>
      ) : (
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleConfirm}
        >
          <span>✓</span>
          <span>{t.thisIsRightBtn}</span>
        </button>
      )}
    </div>
  );
};
