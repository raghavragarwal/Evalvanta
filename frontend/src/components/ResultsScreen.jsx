const ASSESSMENT_COLORS = {
  Strong: { bg: "var(--sage-soft)", fg: "var(--sage)" },
  Solid: { bg: "var(--sage-soft)", fg: "var(--sage)" },
  Developing: { bg: "var(--amber-soft)", fg: "var(--amber)" },
  "Needs Work": { bg: "#F5DCDC", fg: "#7A2626" },
};

export default function ResultsScreen({ results, onRestart }) {
  const assessmentStyle = ASSESSMENT_COLORS[results.overall_assessment] || {
    bg: "var(--accent-soft)",
    fg: "var(--accent)",
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.mono}>SESSION COMPLETE</div>
      <h1 style={styles.heading}>Interview summary</h1>

      {results.overall_assessment && (
        <span
          style={{
            ...styles.badge,
            background: assessmentStyle.bg,
            color: assessmentStyle.fg,
          }}
        >
          {results.overall_assessment}
        </span>
      )}

      {results.summary_text && <p style={styles.summaryText}>{results.summary_text}</p>}

      {(results.strengths?.length > 0 || results.gaps?.length > 0) && (
        <div style={styles.insightsGrid}>
          {results.strengths?.length > 0 && (
            <div style={styles.insightCol}>
              <div style={styles.insightLabel}>Strengths</div>
              <ul style={styles.list}>
                {results.strengths.map((s, i) => (
                  <li key={i} style={styles.listItem}>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {results.gaps?.length > 0 && (
            <div style={styles.insightCol}>
              <div style={styles.insightLabel}>Areas to develop</div>
              <ul style={styles.list}>
                {results.gaps.map((g, i) => (
                  <li key={i} style={styles.listItem}>
                    {g}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div style={styles.divider} />

      <div style={styles.mono}>FULL TRANSCRIPT</div>
      <div style={styles.transcript}>
        {results.transcript.map((item) => (
          <div key={item.question_order} style={styles.qaBlock}>
            <div style={styles.qaMono}>Q{item.question_order}</div>
            <div style={styles.qaQuestion}>{item.question_text}</div>
            <div style={styles.qaAnswer}>
              {item.answer_text || <em style={{ color: "var(--ink-soft)" }}>No answer recorded</em>}
            </div>
            {item.retrieved_chunk_ids?.length > 0 && (
              <div style={styles.chunkRow}>
                {item.retrieved_chunk_ids.map((id) => (
                  <span key={id} style={styles.chunkTag}>
                    {id}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <button onClick={onRestart} style={styles.button}>
        Start another session
      </button>
    </div>
  );
}

const styles = {
  wrap: { maxWidth: 680, margin: "0 auto", padding: "56px 24px 96px" },
  mono: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    letterSpacing: "0.06em",
    color: "var(--ink-soft)",
    marginBottom: 12,
  },
  heading: {
    fontFamily: "var(--font-display)",
    fontSize: 36,
    fontWeight: 500,
    margin: "0 0 20px",
    color: "var(--ink)",
  },
  badge: {
    display: "inline-block",
    padding: "6px 14px",
    borderRadius: 100,
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 20,
  },
  summaryText: {
    fontSize: 16,
    lineHeight: 1.65,
    color: "var(--ink)",
    marginBottom: 32,
    maxWidth: 600,
  },
  insightsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 32,
    marginBottom: 40,
  },
  insightCol: {},
  insightLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--ink-soft)",
    marginBottom: 10,
  },
  list: { margin: 0, paddingLeft: 18 },
  listItem: { fontSize: 14, lineHeight: 1.6, marginBottom: 6, color: "var(--ink)" },
  divider: { height: 1, background: "var(--line)", margin: "12px 0 32px" },
  transcript: { display: "flex", flexDirection: "column", gap: 28, marginBottom: 40 },
  qaBlock: {
    padding: "20px",
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: 6,
  },
  qaMono: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--accent)",
    marginBottom: 8,
  },
  qaQuestion: {
    fontSize: 16,
    fontWeight: 600,
    marginBottom: 10,
    color: "var(--ink)",
    lineHeight: 1.5,
  },
  qaAnswer: { fontSize: 14, lineHeight: 1.6, color: "var(--ink-soft)", marginBottom: 12 },
  chunkRow: { display: "flex", flexWrap: "wrap", gap: 6 },
  chunkTag: {
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    padding: "3px 8px",
    background: "var(--accent-soft)",
    color: "var(--accent)",
    borderRadius: 3,
  },
  button: {
    padding: "14px 20px",
    fontSize: 15,
    fontWeight: 600,
    color: "var(--ink)",
    background: "transparent",
    border: "1px solid var(--line)",
    borderRadius: 4,
    cursor: "pointer",
  },
};
