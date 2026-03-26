import { useState } from "react";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import "./App.css";

const formatCurrency = (value) => {
  const numeric = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(numeric) ? numeric : 0);
};

function App() {
  const [cash_balance, setCashBalance] = useState(0);
  const [obligations, setObligations] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const analyzedCashBalance = Number(result?.cash_balance);
  const displayCashBalance = Number.isFinite(analyzedCashBalance)
    ? analyzedCashBalance
    : cash_balance;

  const handleCashBalance = (value) => {
    setCashBalance(value);
  };

  const handleAddTransaction = (transaction) => {
    if (!transaction || typeof transaction !== "object") {
      return { ok: false, error: "Invalid transaction." };
    }

    const amount = Number(transaction.amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      return { ok: false, error: "Enter a valid transaction amount." };
    }

    const currentCash = Number(cash_balance);
    const cashIsValid = Number.isFinite(currentCash);

    if (transaction.type === "immediate_debit") {
      if (!cashIsValid) {
        return { ok: false, error: "Cash balance is invalid." };
      }
      if (currentCash < amount) {
        return {
          ok: false,
          error: "Insufficient cash balance for this payment.",
        };
      }
      setCashBalance(currentCash - amount);
    }

    if (transaction.type === "immediate_credit") {
      const baseCash = cashIsValid ? currentCash : 0;
      setCashBalance(baseCash + amount);
    }

    setTransactions((prev) => [...prev, transaction]);
    return { ok: true };
  };

  const handleImportFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/upload/document", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`);
    }

    const data = await response.json();
    const importedTransactions = Array.isArray(data.transactions)
      ? data.transactions
      : [];
    const importedObligations = Array.isArray(data.obligations)
      ? data.obligations
      : [];
    const sourceType = String(data.source_type || "").toLowerCase();
    const parsedCashBalance = Number(data.cash_balance);
    const hasCsvBalance = sourceType === "csv" && Number.isFinite(parsedCashBalance);
    let transactionsToStore = importedTransactions;

    // Only CSV imports are expected to provide bank-statement cash context.
    if (hasCsvBalance) {
      setCashBalance(parsedCashBalance);

      // Avoid double counting: when using CSV closing balance, keep only due transactions.
      transactionsToStore = importedTransactions.filter((item) =>
        String(item?.type || "").toLowerCase().startsWith("due_"),
      );
    }

    if (hasCsvBalance) {
      // Replace previous imported timeline to prevent repeated-import accumulation.
      setTransactions(transactionsToStore);
    } else if (transactionsToStore.length > 0) {
      setTransactions((prev) => [...prev, ...transactionsToStore]);
    }

    if (hasCsvBalance) {
      setObligations(importedObligations);
    } else if (importedObligations.length > 0) {
      setObligations((prev) => [...prev, ...importedObligations]);
    }

    return transactionsToStore.length + importedObligations.length;
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    const dueTransactions = transactions.filter((item) =>
      String(item?.type || "").toLowerCase().startsWith("due_"),
    );

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          cash_balance: Number(cash_balance) || 0,
          obligations: obligations,
          transactions: dueTransactions,
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to analyze obligations.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <div className="grid-glow" />
      <div className="app-wrap dashboard-grid">
        <aside className="side-nav panel-like">
          <h2 className="brand">CashClear</h2>
          <nav>
            <button className="nav-link nav-link-active" type="button">
              <span className="nav-icon">▦</span>
              Dashboard
            </button>
            <button className="nav-link" type="button">
              <span className="nav-icon">◉</span>
              My Account
            </button>
            <button className="nav-link" type="button">
              <span className="nav-icon">◎</span>
              Team
            </button>
            <button className="nav-link" type="button">
              <span className="nav-icon">▤</span>
              Reports
            </button>
          </nav>
          <div className="side-footer">Decision Engine v1</div>
        </aside>

        <section className="content-area">
          <header className="hero panel-like">
            <div>
              <h1 className="app-title">CashClear Decision Engine</h1>
              <p className="app-subtitle">
                Prioritize obligations, estimate risk, and protect working
                capital.
              </p>
            </div>
            <div className="hero-stats">
              <div>
                <p className="mini-label">Cash Balance</p>
                <p className="mini-value">{formatCurrency(displayCashBalance)}</p>
              </div>
              <div>
                <p className="mini-label">Transactions Added</p>
                <p className="mini-value">{transactions.length}</p>
              </div>
            </div>
          </header>

          <InputForm
            cashBalance={cash_balance}
            onCashBalance={handleCashBalance}
            onAddTransaction={handleAddTransaction}
            onImportFile={handleImportFile}
            onAnalyze={handleAnalyze}
          />

          {loading && (
            <div className="state-block state-loading">
              <p>Analyzing...</p>
            </div>
          )}

          {error && <p className="state-block state-error">{error}</p>}

          {result && (
            <div className="results-wrap">
              <Results analysisResult={result} />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default App;
