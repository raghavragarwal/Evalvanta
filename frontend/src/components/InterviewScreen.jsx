import { useState } from "react";

export default function InterviewScreen({ question, onAnswer, loading, error }) {
  const [answer, setAnswer] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!answer.trim()) return;
    onAnswer(answer);
    setAnswer("");
  }

  const dots = Array.from({ length: question.questions_total }, (_, i) => i + 1);

  return (
    <div style={styles.wrap}>
      <div style={styles.rail}>
        {dots.map((n) => (
          <div key={n} style={styles.railItem}>
            <div
              style={{
                ...styles.dot,
                ...(n < question.question_order
                  ? styles.dotDone
                  : n === question.question_order
                  ? styles.dotActive
                  : styles.dotPending),
              }}
            />
            {n < dots.length && <div style={styles.railLine} />}
          </div>
        ))}
      </div>

      <div style={styles.content}>
        <div style={styles.mono}>
          QUESTION {question.question_order} OF {question.questions_total}
        </div>
        <h2 style={styles.questionText}>{question.question_text}</h2>

        <form onSubmit={handleSubmit} style={styles.form}>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Walk through your answer here…"
            rows={8}
            style={styles.textarea}
            autoFocus
          />
          {error && <div style={styles.errorBox}>{error}</div>}
          <button type="submit" disabled={!answer.trim() || loading} style={styles.button}>
            {loading
              ? "Thinking of the next question…"
              : question.is_last
              ? "Submit final answer"
              : "Submit & continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  wrap: {
    maxWidth: 720,
    margin: "0 auto",
    padding: "56px 24px",
    display: "flex",
    gap: 28,
  },
  rail: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: 6,
  },
  railItem: { display: "flex", flexDirection: "column", alignItems: "center" },
  dot: { width: 12, height: 12, borderRadius: "50%", flexShrink: 0 },
  dotDone: { background: "var(--sage)" },
  dotActive: {
    background: "var(--accent)",
    boxShadow: "0 0 0 4px var(--accent-soft)",
  },
  dotPending: { background: "var(--line)" },
  railLine: { width: 2, height: 28, background: "var(--line)", margin: "4px 0" },
  content: { flex: 1, minWidth: 0 },
  mono: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    letterSpacing: "0.06em",
    color: "var(--ink-soft)",
    marginBottom: 14,
  },
  questionText: {
    fontFamily: "var(--font-display)",
    fontSize: 28,
    lineHeight: 1.35,
    fontWeight: 500,
    margin: "0 0 32px",
    color: "var(--ink)",
  },
  form: { display: "flex", flexDirection: "column", gap: 16 },
  textarea: {
    padding: "16px",
    fontSize: 15,
    lineHeight: 1.6,
    fontFamily: "var(--font-body)",
    border: "1px solid var(--line)",
    borderRadius: 4,
    background: "var(--paper-raised)",
    color: "var(--ink)",
    resize: "vertical",
  },
  errorBox: {
    padding: "12px 14px",
    background: "#F5DCDC",
    border: "1px solid #D98C8C",
    borderRadius: 4,
    fontSize: 14,
    color: "#7A2626",
  },
  button: {
    alignSelf: "flex-start",
    padding: "14px 20px",
    fontSize: 15,
    fontWeight: 600,
    color: "#fff",
    background: "var(--accent)",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
  },
};
