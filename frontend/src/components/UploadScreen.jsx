import { useState } from "react";

const ROLES = [
  { value: "backend_engineer", label: "Backend Engineer" },
  { value: "ai_ml_engineer", label: "AI / ML Engineer" },
];

export default function UploadScreen({ onSubmit, loading, error }) {
  const [role, setRole] = useState(ROLES[0].value);
  const [name, setName] = useState("");
  const [file, setFile] = useState(null);

  function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    onSubmit({ role, name, resumeFile: file });
  }

  return (
    <div style={styles.wrap}>
      <div style={styles.eyebrowRow}>
        <span style={styles.mono}>EVALVANTA</span>
      </div>
      <h1 style={styles.heading}>
        Let's see how your background <em style={{ fontStyle: "italic" }}>meets the role.</em>
      </h1>
      <p style={styles.sub}>
        Upload a resume and pick a role. The interview questions that follow are generated from
        your background and a role-specific knowledge base -- not a fixed question bank.
      </p>

      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          Target role
          <select value={role} onChange={(e) => setRole(e.target.value)} style={styles.select}>
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>

        <label style={styles.label}>
          Your name (optional)
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Doe"
            style={styles.input}
          />
        </label>

        <label style={styles.label}>
          Resume (PDF or text)
          <div style={styles.dropzone}>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              style={styles.fileInput}
            />
            <span style={styles.mono}>{file ? file.name : "Choose a file"}</span>
          </div>
        </label>

        {error && <div style={styles.errorBox}>{error}</div>}

        <button type="submit" disabled={!file || loading} style={styles.button}>
          {loading ? "Reading your resume…" : "Start interview"}
        </button>
      </form>
    </div>
  );
}

const styles = {
  wrap: { maxWidth: 560, margin: "0 auto", padding: "72px 24px" },
  eyebrowRow: { marginBottom: 20 },
  mono: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    letterSpacing: "0.06em",
    color: "var(--ink-soft)",
  },
  heading: {
    fontFamily: "var(--font-display)",
    fontSize: 40,
    lineHeight: 1.15,
    fontWeight: 500,
    margin: "0 0 16px",
    color: "var(--ink)",
  },
  sub: {
    fontSize: 16,
    lineHeight: 1.6,
    color: "var(--ink-soft)",
    maxWidth: 460,
    margin: "0 0 40px",
  },
  form: { display: "flex", flexDirection: "column", gap: 20 },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--ink)",
  },
  select: {
    padding: "12px 14px",
    fontSize: 15,
    fontFamily: "var(--font-body)",
    border: "1px solid var(--line)",
    borderRadius: 4,
    background: "var(--paper-raised)",
    color: "var(--ink)",
  },
  input: {
    padding: "12px 14px",
    fontSize: 15,
    fontFamily: "var(--font-body)",
    border: "1px solid var(--line)",
    borderRadius: 4,
    background: "var(--paper-raised)",
    color: "var(--ink)",
  },
  dropzone: {
    position: "relative",
    border: "1px dashed var(--line)",
    borderRadius: 4,
    padding: "18px 14px",
    background: "var(--paper-raised)",
  },
  fileInput: {
    position: "absolute",
    inset: 0,
    opacity: 0,
    cursor: "pointer",
    width: "100%",
    height: "100%",
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
    marginTop: 8,
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
