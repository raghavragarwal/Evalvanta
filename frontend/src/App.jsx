import { useState } from "react";
import UploadScreen from "./components/UploadScreen.jsx";
import InterviewScreen from "./components/InterviewScreen.jsx";
import ResultsScreen from "./components/ResultsScreen.jsx";
import { createCandidate, startInterview, submitAnswer, getResults } from "./api.js";

// Stages: "upload" -> "interview" -> "results"
export default function App() {
  const [stage, setStage] = useState("upload");
  const [candidateId, setCandidateId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleUploadSubmit({ role, name, resumeFile }) {
    setLoading(true);
    setError(null);
    try {
      const candidate = await createCandidate({ role, name, resumeFile });
      setCandidateId(candidate.candidate_id);

      const firstQuestion = await startInterview(candidate.candidate_id);
      setSessionId(firstQuestion.session_id);
      setCurrentQuestion(firstQuestion);
      setStage("interview");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswer(answerText) {
    setLoading(true);
    setError(null);
    try {
      const response = await submitAnswer({
        sessionId,
        questionId: currentQuestion.question_id,
        answerText,
      });

      if (response.session_complete) {
        const finalResults = await getResults(sessionId);
        setResults(finalResults);
        setStage("results");
      } else {
        setCurrentQuestion(response.next_question);
      }
    } catch (err) {
      setError(err.message || "Something went wrong submitting your answer.");
    } finally {
      setLoading(false);
    }
  }

  function handleRestart() {
    setStage("upload");
    setCandidateId(null);
    setSessionId(null);
    setCurrentQuestion(null);
    setResults(null);
    setError(null);
  }

  return (
    <div>
      {stage === "upload" && (
        <UploadScreen onSubmit={handleUploadSubmit} loading={loading} error={error} />
      )}
      {stage === "interview" && currentQuestion && (
        <InterviewScreen
          question={currentQuestion}
          onAnswer={handleAnswer}
          loading={loading}
          error={error}
        />
      )}
      {stage === "results" && results && (
        <ResultsScreen results={results} onRestart={handleRestart} />
      )}
    </div>
  );
}
