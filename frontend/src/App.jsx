import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const TRADITION_COLORS = {
  Vedic: "#e8a838",
  Epic: "#58b4e8",
  Dharmashastra: "#a8e858",
  Arthashastra: "#e8586e",
  Buddhist: "#c858e8",
  Jain: "#58e8c8",
};

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
    <span className="text-badge" style={{ backgroundColor: color + "18", borderColor: color + "44", color }}>
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
        <span className="verse-toggle">{open ? "▾" : "▸"}</span>
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
        {data.compare_mode && <span className="compare-label">Comparison Mode</span>}
        {textNames.map((t) => {
          const verse = data.verses.find((v) => v.text_name === t);
          return <TextBadge key={t} textName={t} tradition={verse?.tradition} />;
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

export default function App() {
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

  function toggleCompareText(name) {
    setCompareTexts((prev) =>
      prev.includes(name) ? prev.filter((t) => t !== name) : [...prev, name]
    );
  }

  async function handleAsk(q) {
    const text = (q || question).trim();
    if (!text) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const body = { question: text };
    if (compareMode && compareTexts.length > 1) {
      body.compare_texts = compareTexts;
    } else if (selectedText) {
      body.text_filter = selectedText;
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

  function handleSubmit(e) {
    e.preventDefault();
    handleAsk();
  }

  function handleSample(q) {
    setQuestion(q);
    handleAsk(q);
  }

  const activeSamples = compareMode
    ? Object.values(SAMPLE_QUESTIONS).flat().slice(0, 4)
    : SAMPLE_QUESTIONS[selectedText] || [];

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="title-icon">ॐ</span> Scripture Wisdom
          </h1>
          <p className="app-subtitle">
            Ask questions about Indian scriptures — answers grounded strictly in
            primary source text
          </p>
        </div>
      </header>

      <main className="app-main">
        {/* Text Selector */}
        <div className="text-selector">
          <div className="selector-row">
            <div className="selector-tabs">
              {!compareMode &&
                texts.map((t) => (
                  <button
                    key={t.name}
                    className={`tab-button ${selectedText === t.name ? "active" : ""}`}
                    onClick={() => setSelectedText(t.name)}
                    style={
                      selectedText === t.name
                        ? { borderBottomColor: TRADITION_COLORS[t.tradition] || "#888" }
                        : {}
                    }
                  >
                    {t.name}
                    <span className="tab-count">{t.entry_count.toLocaleString()}</span>
                  </button>
                ))}
              {compareMode &&
                texts.map((t) => (
                  <button
                    key={t.name}
                    className={`tab-button compare-tab ${compareTexts.includes(t.name) ? "active" : ""}`}
                    onClick={() => toggleCompareText(t.name)}
                    style={
                      compareTexts.includes(t.name)
                        ? { borderBottomColor: TRADITION_COLORS[t.tradition] || "#888" }
                        : {}
                    }
                  >
                    {compareTexts.includes(t.name) ? "✓ " : ""}
                    {t.name}
                  </button>
                ))}
            </div>
            <button
              className={`compare-toggle ${compareMode ? "active" : ""}`}
              onClick={() => {
                setCompareMode(!compareMode);
                if (!compareMode) setCompareTexts([]);
              }}
            >
              {compareMode ? "✕ Compare" : "⇆ Compare"}
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
                <button key={q} className="sample-button" onClick={() => handleSample(q)}>
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

        <footer className="app-footer">
          <p>
            Sources: Bhagavad Gita (Prabhupada) · Upanishads (Nikhilananda) ·
            Manusmriti (Bühler) · Arthashastra (Shamasastry) · Mahabharata
            (Menon) · Ramayana (Griffith)
          </p>
          <p className="footer-note">
            All answers are generated from primary source text only. No invented
            content.
          </p>
        </footer>
      </main>
    </div>
  );
}
