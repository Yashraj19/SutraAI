import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/* ========================================
   Data Constants
   ======================================== */

const TRADITION_COLORS = {
  Vedic: "#e8a838",
  Epic: "#58b4e8",
  Dharmashastra: "#a8e858",
  Arthashastra: "#e8586e",
  Buddhist: "#c858e8",
  Jain: "#58e8c8",
};

const SCRIPTURE_INFO = {
  "Bhagavad Gita": {
    description: "A 700-verse dialogue between Arjuna and Krishna on the battlefield, exploring duty, devotion, and the nature of reality.",
    tradition: "Vedic",
  },
  Upanishads: {
    description: "Philosophical treatises exploring Brahman, Atman, and the ultimate nature of consciousness and reality.",
    tradition: "Vedic",
  },
  Manusmriti: {
    description: "An ancient legal text codifying social laws, duties of the four varnas, and rituals of dharmic life.",
    tradition: "Dharmashastra",
  },
  Arthashastra: {
    description: "Kautilya's treatise on statecraft, economics, military strategy, and the art of governance.",
    tradition: "Arthashastra",
  },
  Mahabharata: {
    description: "The great epic of the Kuru dynasty — war, diplomacy, dharma, and the human condition across 100,000 verses.",
    tradition: "Epic",
  },
  Ramayana: {
    description: "The journey of Rama — exile, devotion, the battle against Ravana, and the ideals of righteous kingship.",
    tradition: "Epic",
  },
};

const THEME_CARDS = [
  {
    id: "dharma",
    title: "Dharma & Duty",
    subtitle: "The moral order",
    description: "What the scriptures say about righteous conduct, moral obligation, and cosmic law.",
    question: "What is dharma and how should one follow it?",
    textFilter: "Bhagavad Gita",
    accentColor: "#e8a838",
  },
  {
    id: "karma",
    title: "Karma & Rebirth",
    subtitle: "Action and consequence",
    description: "The cycle of action, its fruits, and the path to liberation from samsara.",
    question: "What is the law of karma and how does it relate to rebirth?",
    textFilter: "Upanishads",
    accentColor: "#c858e8",
  },
  {
    id: "devotion",
    title: "Love & Devotion",
    subtitle: "Bhakti and surrender",
    description: "The path of devotion, surrender to the divine, and the power of love in spiritual life.",
    question: "What does Krishna say about devotion and surrender?",
    textFilter: "Bhagavad Gita",
    accentColor: "#e8586e",
  },
  {
    id: "strategy",
    title: "War & Strategy",
    subtitle: "Power and statecraft",
    description: "Military tactics, political strategy, and the ethics of warfare in ancient India.",
    question: "What are the principles of warfare and military strategy?",
    textFilter: "Arthashastra",
    accentColor: "#58b4e8",
  },
  {
    id: "cosmos",
    title: "Creation & Cosmos",
    subtitle: "Origins of existence",
    description: "How the universe came into being, the nature of time, and the cosmic cycles of creation.",
    question: "How was the universe created?",
    textFilter: "Upanishads",
    accentColor: "#a8e858",
  },
  {
    id: "self",
    title: "Self & Consciousness",
    subtitle: "The inner journey",
    description: "The nature of the self, consciousness, meditation, and the path to self-realization.",
    question: "What is the relationship between Atman and Brahman?",
    textFilter: "Upanishads",
    accentColor: "#f0c060",
  },
];

const CROSS_TEXT_SHOWDOWNS = [
  {
    title: "Duty Across Traditions",
    question: "What is the nature of duty and how should one fulfill it?",
    compareTexts: ["Bhagavad Gita", "Manusmriti", "Arthashastra"],
    accentColor: "#e8a838",
  },
  {
    title: "The Ideal Ruler",
    question: "What qualities should an ideal king or ruler possess?",
    compareTexts: ["Arthashastra", "Mahabharata", "Ramayana"],
    accentColor: "#58b4e8",
  },
  {
    title: "Justice & Punishment",
    question: "What do the texts say about justice and punishment?",
    compareTexts: ["Manusmriti", "Arthashastra", "Mahabharata"],
    accentColor: "#a8e858",
  },
];

const SURPRISE_POOL = [
  { question: "What is the nature of the soul?", textFilter: "Bhagavad Gita" },
  { question: "What does Krishna say about duty?", textFilter: "Bhagavad Gita" },
  { question: "What are the three gunas?", textFilter: "Bhagavad Gita" },
  { question: "What is Brahman?", textFilter: "Upanishads" },
  { question: "What is the nature of consciousness?", textFilter: "Upanishads" },
  { question: "What are the duties of a king?", textFilter: "Arthashastra" },
  { question: "How should a treasury be managed?", textFilter: "Arthashastra" },
  { question: "What is the role of spies?", textFilter: "Arthashastra" },
  { question: "What are the sources of dharma?", textFilter: "Manusmriti" },
  { question: "What are the samskaras?", textFilter: "Manusmriti" },
  { question: "Who are the Pandavas?", textFilter: "Mahabharata" },
  { question: "What happened at the dice game?", textFilter: "Mahabharata" },
  { question: "What is the story of Bhishma?", textFilter: "Mahabharata" },
  { question: "Who is Rama?", textFilter: "Ramayana" },
  { question: "What happened to Sita?", textFilter: "Ramayana" },
  { question: "How was Ravana defeated?", textFilter: "Ramayana" },
];

const SAMPLE_QUESTIONS = {
  "Bhagavad Gita": [
    "What is the nature of the soul?",
    "What does Krishna say about duty?",
    "What are the three gunas?",
  ],
  Upanishads: [
    "What is Brahman?",
    "What is the relationship between Atman and Brahman?",
    "What is the nature of consciousness?",
  ],
  Manusmriti: [
    "What are the duties of a Brahmana?",
    "What are the sources of dharma?",
    "What are the samskaras?",
  ],
  Arthashastra: [
    "What are the duties of a king?",
    "How should a treasury be managed?",
    "What is the role of spies?",
  ],
  Mahabharata: [
    "Who are the Pandavas?",
    "What happened at the dice game?",
    "What is the story of Bhishma?",
  ],
  Ramayana: [
    "Who is Rama?",
    "What happened to Sita?",
    "How was Ravana defeated?",
  ],
};

/* ========================================
   Shared Components
   ======================================== */

function TraditionBadge({ tradition }) {
  const color = TRADITION_COLORS[tradition] || "#888";
  return (
    <span className="tradition-badge" style={{ borderColor: color, color }}>
      {tradition}
    </span>
  );
}

function TextBadge({ textName, tradition }) {
  const color = TRADITION_COLORS[tradition] || "#888";
  return (
    <span
      className="text-badge"
      style={{
        backgroundColor: color + "18",
        borderColor: color + "44",
        color,
      }}
    >
      {textName}
    </span>
  );
}

function VerseCard({ verse, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen || false);
  const color = TRADITION_COLORS[verse.tradition] || "#888";

  return (
    <div className="verse-card" style={{ borderLeftColor: color }}>
      <button className="verse-header" onClick={() => setOpen(!open)}>
        <span className="verse-ref" style={{ color }}>
          {verse.text_name} {verse.chapter}.{verse.verse}
        </span>
        <TraditionBadge tradition={verse.tradition} />
        <span className="verse-source">{verse.translation_source}</span>
        <span className="verse-toggle">{open ? "\u25BE" : "\u25B8"}</span>
      </button>
      {open && (
        <div className="verse-body">
          {verse.section && (
            <p className="verse-section">{verse.section}</p>
          )}
          <p className="verse-translation">"{verse.translation}"</p>
          <div className="verse-meta">
            Relevance: {(verse.relevance_score * 100).toFixed(0)}%
          </div>
        </div>
      )}
    </div>
  );
}

function AnswerDisplay({ data }) {
  if (!data) return null;

  const traditions = [...new Set(data.verses.map((v) => v.tradition))];
  const textNames = [...new Set(data.verses.map((v) => v.text_name))];

  return (
    <div className="answer-container">
      <div className="answer-meta-bar">
        {data.compare_mode && (
          <span className="compare-label">Comparison Mode</span>
        )}
        {textNames.map((t) => {
          const verse = data.verses.find((v) => v.text_name === t);
          return (
            <TextBadge key={t} textName={t} tradition={verse?.tradition} />
          );
        })}
      </div>

      <div className="answer-section answer-main">
        <ReactMarkdown>{data.answer}</ReactMarkdown>
      </div>

      {data.verses.length > 0 && (
        <div className="answer-section">
          <h3 className="section-title">
            Referenced Passages ({data.verses.length})
          </h3>
          <div className="verses-list">
            {data.verses.map((v, i) => (
              <VerseCard
                key={`${v.text_name}-${v.chapter}-${v.verse}-${i}`}
                verse={v}
                defaultOpen={i < 3}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ========================================
   Main App
   ======================================== */

export default function App() {
  const [view, setView] = useState("home");
  const [texts, setTexts] = useState([]);
  const [selectedText, setSelectedText] = useState("");
  const [compareMode, setCompareMode] = useState(false);
  const [compareTexts, setCompareTexts] = useState([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/texts`)
      .then((r) => r.json())
      .then((data) => {
        setTexts(data);
        if (data.length > 0) setSelectedText(data[0].name);
      })
      .catch(() => {});
  }, []);

  /* Navigation helpers */
  function navigateToAsk({ text, q, compare, compareTextsList } = {}) {
    const finalText = text || selectedText;
    const finalCompare = compare || false;
    const finalCompareTexts = compareTextsList || [];

    setSelectedText(finalText);
    setCompareMode(finalCompare);
    setCompareTexts(finalCompareTexts);
    setResult(null);
    setError(null);
    setView("ask");

    if (q) {
      setQuestion(q);
      // Fire the query with direct parameters to avoid stale state
      fireQuery(q, {
        textFilter: finalCompare ? null : finalText,
        compareTexts: finalCompare ? finalCompareTexts : null,
      });
    } else {
      setQuestion("");
    }
  }

  function navigateToHome() {
    setView("home");
    setResult(null);
    setError(null);
    setQuestion("");
  }

  /* Core API call */
  async function fireQuery(q, overrides = {}) {
    const text = q.trim();
    if (!text) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const body = { question: text };
    if (overrides.compareTexts && overrides.compareTexts.length > 1) {
      body.compare_texts = overrides.compareTexts;
    } else if (overrides.textFilter) {
      body.text_filter = overrides.textFilter;
    }

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `Server error (${res.status})`);
      }

      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /* Ask-view query (uses current state) */
  async function handleAsk(q) {
    const text = (q || question).trim();
    if (!text) return;

    const overrides = {};
    if (compareMode && compareTexts.length > 1) {
      overrides.compareTexts = compareTexts;
    } else if (selectedText) {
      overrides.textFilter = selectedText;
    }

    fireQuery(text, overrides);
  }

  function handleSubmit(e) {
    e.preventDefault();
    handleAsk();
  }

  function handleSample(q) {
    setQuestion(q);
    handleAsk(q);
  }

  function toggleCompareText(name) {
    setCompareTexts((prev) =>
      prev.includes(name) ? prev.filter((t) => t !== name) : [...prev, name]
    );
  }

  function handleSurprise() {
    const pick = SURPRISE_POOL[Math.floor(Math.random() * SURPRISE_POOL.length)];
    navigateToAsk({ text: pick.textFilter, q: pick.question });
  }

  function handleHeroSearch(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    navigateToAsk({ q });
  }

  /* ========================================
     Home View
     ======================================== */
  function HomeView() {
    return (
      <div className="view-container" key="home">
        {/* Hero */}
        <section className="hero">
          <h1 className="hero-title">SutraAI</h1>
          <p className="hero-subtitle">
            Explore six ancient Indian scriptures through AI-powered search.
            Every answer grounded in primary source text.
          </p>
          <form className="hero-search" onSubmit={handleHeroSearch}>
            <input
              type="text"
              className="hero-search-input"
              placeholder="Ask anything about the scriptures..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              maxLength={500}
            />
            <button
              type="submit"
              className="hero-search-btn"
              disabled={!question.trim()}
            >
              Ask
            </button>
          </form>
          <div className="hero-actions">
            <button className="surprise-btn" onClick={handleSurprise}>
              Surprise Me
            </button>
          </div>
        </section>

        <div className="home-content">
          {/* Theme Exploration */}
          <section className="home-section">
            <h2 className="section-heading">Explore by Theme</h2>
            <p className="section-subheading">
              Dive into the big ideas that connect these ancient texts.
            </p>
            <div className="theme-grid">
              {THEME_CARDS.map((card) => (
                <div
                  key={card.id}
                  className="glass-card theme-card"
                  onClick={() =>
                    navigateToAsk({ text: card.textFilter, q: card.question })
                  }
                >
                  <div
                    className="theme-card-accent"
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      right: 0,
                      height: "3px",
                      background: card.accentColor,
                      borderRadius: "14px 14px 0 0",
                    }}
                  />
                  <div
                    className="theme-card-title"
                    style={{ color: card.accentColor }}
                  >
                    {card.title}
                  </div>
                  <div className="theme-card-subtitle">{card.subtitle}</div>
                  <div className="theme-card-desc">{card.description}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Scripture Showcase */}
          <section className="home-section">
            <h2 className="section-heading">The Scriptures</h2>
            <p className="section-subheading">
              Six foundational texts spanning philosophy, law, statecraft, and
              epic narrative.
            </p>
            <div className="scripture-grid">
              {texts.map((t) => {
                const info = SCRIPTURE_INFO[t.name] || {};
                const color = TRADITION_COLORS[t.tradition] || "#888";
                return (
                  <div
                    key={t.name}
                    className="glass-card scripture-card"
                    onClick={() => navigateToAsk({ text: t.name })}
                  >
                    <div className="scripture-card-header">
                      <span
                        className="scripture-dot"
                        style={{ backgroundColor: color }}
                      />
                      <span className="scripture-card-name">{t.name}</span>
                    </div>
                    <div className="scripture-card-desc">
                      {info.description || ""}
                    </div>
                    <div className="scripture-card-footer">
                      <span className="scripture-card-count">
                        {t.entry_count.toLocaleString()} passages
                      </span>
                      <span className="scripture-card-link">Explore →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Cross-Text Showdowns */}
          <section className="home-section">
            <h2 className="section-heading">Cross-Text Showdowns</h2>
            <p className="section-subheading">
              Compare how different scriptures address the same question.
            </p>
            <div className="showdown-grid">
              {CROSS_TEXT_SHOWDOWNS.map((s, i) => (
                <div
                  key={i}
                  className="glass-card showdown-card"
                  onClick={() =>
                    navigateToAsk({
                      q: s.question,
                      compare: true,
                      compareTextsList: s.compareTexts,
                    })
                  }
                >
                  <div className="showdown-card-title">{s.title}</div>
                  <div className="showdown-card-texts">
                    {s.compareTexts.map((name) => (
                      <span key={name} className="showdown-pill">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    );
  }

  /* ========================================
     Ask View
     ======================================== */
  function AskView() {
    const activeSamples = compareMode
      ? Object.values(SAMPLE_QUESTIONS).flat().slice(0, 4)
      : SAMPLE_QUESTIONS[selectedText] || [];

    return (
      <div className="view-container" key="ask">
        <div className="ask-view">
          {/* Text Selector */}
          <div className="text-selector">
            <div className="selector-pills">
              {texts.map((t) => {
                const color = TRADITION_COLORS[t.tradition] || "#888";
                const isActive = compareMode
                  ? compareTexts.includes(t.name)
                  : selectedText === t.name;

                return (
                  <button
                    key={t.name}
                    className={`pill-button ${isActive ? "active" : ""}`}
                    onClick={() =>
                      compareMode
                        ? toggleCompareText(t.name)
                        : setSelectedText(t.name)
                    }
                    style={
                      isActive
                        ? {
                            backgroundColor: color + "18",
                            borderColor: color + "66",
                            color: color,
                          }
                        : {}
                    }
                  >
                    <span
                      className="pill-dot"
                      style={{ backgroundColor: color }}
                    />
                    {compareMode && isActive && (
                      <span className="pill-check">✓</span>
                    )}
                    {t.name}
                    <span className="pill-count">
                      {t.entry_count.toLocaleString()}
                    </span>
                  </button>
                );
              })}
              <button
                className={`pill-button compare-toggle ${compareMode ? "active" : ""}`}
                onClick={() => {
                  setCompareMode(!compareMode);
                  if (!compareMode) setCompareTexts([]);
                }}
              >
                {compareMode ? "\u2715 Compare" : "\u21C6 Compare"}
              </button>
            </div>
            {compareMode && (
              <p className="compare-hint">
                Select 2+ texts to compare. {compareTexts.length} selected.
              </p>
            )}
          </div>

          {/* Search */}
          <form className="search-form" onSubmit={handleSubmit}>
            <div className="input-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder={
                  compareMode
                    ? "Ask a question to compare across texts..."
                    : `Ask about ${selectedText}...`
                }
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
                maxLength={500}
              />
              <button
                type="submit"
                className="search-button"
                disabled={
                  loading ||
                  !question.trim() ||
                  (compareMode && compareTexts.length < 2)
                }
              >
                {loading ? <span className="spinner" /> : "Ask"}
              </button>
            </div>
          </form>

          {/* Samples */}
          {!result && !loading && !error && activeSamples.length > 0 && (
            <div className="samples">
              <p className="samples-label">Try a question:</p>
              <div className="samples-grid">
                {activeSamples.map((q) => (
                  <button
                    key={q}
                    className="sample-button"
                    onClick={() => handleSample(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="loading-spinner" />
              <p>Searching passages and generating answer...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p>⚠ {error}</p>
            </div>
          )}

          <AnswerDisplay data={result} />
        </div>
      </div>
    );
  }

  /* ========================================
     Render
     ======================================== */
  return (
    <div className="app">
      {/* Mesh Background */}
      <div className="mesh-bg" />

      {/* Nav Bar */}
      <nav className="nav-bar">
        <span className="nav-logo" onClick={navigateToHome}>
          SutraAI
        </span>
        {view === "ask" && (
          <button className="nav-home-btn" onClick={navigateToHome}>
            Home
          </button>
        )}
      </nav>

      {/* Views */}
      {view === "home" ? <HomeView /> : <AskView />}

      {/* Footer */}
      <footer className="app-footer">
        <p>
          Sources: Bhagavad Gita (Prabhupada) · Upanishads (Nikhilananda) ·
          Manusmriti (Bühler) · Arthashastra (Shamasastry) · Mahabharata
          (Menon) · Ramayana (Griffith)
        </p>
        <p className="footer-note">
          SutraAI generates answers from primary source text only. No invented
          content.
        </p>
      </footer>
    </div>
  );
}
