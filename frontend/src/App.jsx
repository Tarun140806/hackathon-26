import { useState } from "react";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import { analyzeObligations } from "./api";
function App() {
  const [cashBalance, setCashBalance] = useState(0)
  const [obligations, setObligations] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCashBalance = (value) => {
    setCashBalance(value)
  }

  const handleAddObligation = (obligation) => {
    setObligations((prev) => [...prev, obligation])
  }

  const handleAnalyze = async () => {
    setLoading(true)
    setError('')

    try {
      const result = await analyzeObligations(cashBalance, obligations)
      setAnalysisResult(result)
    } catch (err) {
      setError(err.message || 'Failed to analyze obligations.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
      <div className="w-full max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="mb-6 text-3xl font-semibold tracking-tight sm:text-4xl">
          CashClear Decision Engine
        </h1>

        <InputForm
          onCashBalance={handleCashBalance}
          onAddObligation={handleAddObligation}
          onAnalyze={handleAnalyze}
        />

        {loading && (
          <div className="mt-8 flex justify-center">
            <p className="text-lg font-medium text-slate-200">
              Analyzing your finances...
            </p>
          </div>
        )}

        {error && <p className="mt-4 text-red-400">{error}</p>}

        {analysisResult && (
          <div className="mt-8">
            <Results analysisResult={analysisResult} />
          </div>
        )}
      </div>
    </main>
  )
}

export default App
