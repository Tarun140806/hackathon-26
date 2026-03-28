import { useState } from "react";
import { useAuth } from "./context/AuthContext";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import AccountPage from "./pages/AccountPage";
import TeamPage from "./pages/TeamPage";
import ReportsPage from "./pages/ReportsPage";
import { saveReport } from "./utils/reports";
import "./App.css";

const formatCurrency = (value) => {
  const numeric = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  }).format(Number.isFinite(numeric) ? numeric : 0);
};

const NAV_ITEMS = [
  { id: "dashboard", icon: "⬡", label: "Dashboard" },
  { id: "account",   icon: "◈", label: "My Account" },
  { id: "team",      icon: "◎", label: "Team" },
  { id: "reports",   icon: "▦", label: "Reports" },
];

function DashboardPage({ currentUser }) {
  const [cash_balance, setCashBalance] = useState(0);
  const [obligations, setObligations]  = useState([]);
  const [result, setResult]            = useState(null);
  const [loading, setLoading]          = useState(false);
  const [error, setError]              = useState("");

  const handleCashBalance    = (v)  => setCashBalance(v);
  const handleAddObligation  = (ob) => setObligations((p) => [...p, ob]);

  const handleImportFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("http://localhost:8000/upload/document", {
      method: "POST", body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    const data = await res.json();
    const imported = Array.isArray(data.obligations) ? data.obligations : [];
    if (typeof data.cash_balance === "number" && Number.isFinite(data.cash_balance))
      setCashBalance(data.cash_balance);
    if (imported.length) setObligations((p) => [...p, ...imported]);
    return imported.length;
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cash_balance, obligations }),
      });
      if (!res.ok) throw new Error(`API error (${res.status})`);
      const data = await res.json();
      setResult(data);
      saveReport(data); // ← auto-save to Reports
    } catch (err) {
      setError(err.message || "Failed to analyze obligations.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Hero */}
      <header className="hero">
        <div className="hero-bg-orb" />
        <div className="hero-content">
          <div className="app-badge">
            <span className="app-badge-dot" />
            AI-Powered
          </div>
          <h1 className="app-title">
            CashClear <span>Decision Engine</span>
          </h1>
          <p className="app-subtitle">
            Prioritize obligations, estimate cash-flow risk, and protect your
            working capital — intelligently.
          </p>
        </div>
        <div className="hero-stats">
          <div className="hero-stat-card">
            <p className="mini-label">Cash Balance</p>
            <p className="mini-value">{formatCurrency(cash_balance)}</p>
          </div>
          <div className="hero-stat-card">
            <p className="mini-label">Obligations</p>
            <p className="mini-value">{obligations.length}</p>
          </div>
          <div className="hero-stat-card">
            <p className="mini-label">Logged in as</p>
            <p className="mini-value" style={{ fontSize: "0.95rem" }}>
              {currentUser.name.split(" ")[0]}
            </p>
          </div>
        </div>
      </header>

      {/* Form */}
      <InputForm
        cashBalance={cash_balance}
        onCashBalance={handleCashBalance}
        onAddObligation={handleAddObligation}
        onImportFile={handleImportFile}
        onAnalyze={handleAnalyze}
      />

      {/* Loading */}
      {loading && (
        <div className="state-block state-loading">
          <span className="loading-spinner" />
          Analyzing your obligations…
        </div>
      )}

      {/* Error */}
      {error && <div className="state-block state-error">⚠ {error}</div>}

      {/* Results */}
      {result && (
        <div className="results-wrap">
          <Results analysisResult={result} />
        </div>
      )}
    </>
  );
}

export default function App() {
  const { currentUser, logout } = useAuth();
  const [activePage, setActivePage] = useState("dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "account": return <AccountPage />;
      case "team":    return <TeamPage />;
      case "reports": return <ReportsPage />;
      default:        return <DashboardPage currentUser={currentUser} />;
    }
  };

  return (
    <main className="app-shell">
      <div className="grid-glow" />
      <div className="app-wrap">

        {/* ── Sidebar ── */}
        <aside className="side-nav">
          {/* Brand */}
          <div className="brand">
            <div className="brand-icon">💎</div>
            <span className="brand-name">CashClear</span>
          </div>

          <span className="nav-section-label">Navigation</span>

          <nav>
            {NAV_ITEMS.map(({ id, icon, label }) => (
              <button
                key={id}
                type="button"
                id={`nav-${id}`}
                className={`nav-link${activePage === id ? " nav-link-active" : ""}`}
                onClick={() => setActivePage(id)}
              >
                <span className="nav-icon">{icon}</span>
                {label}
              </button>
            ))}
          </nav>

          {/* User chip */}
          <div className="side-user-chip">
            <img
              src={currentUser.avatar}
              alt={currentUser.name}
              className="side-user-avatar"
            />
            <div className="side-user-info">
              <p className="side-user-name">{currentUser.name}</p>
              <p className="side-user-role">{currentUser.role}</p>
            </div>
          </div>

          {/* Footer */}
          <div className="side-footer">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="side-footer-badge">
                <span className="side-footer-dot" />
                Engine v1
              </span>
              <button
                id="sidebar-logout-btn"
                className="btn btn-secondary"
                style={{ padding: "4px 10px", fontSize: "0.75rem" }}
                onClick={logout}
              >
                Sign Out
              </button>
            </div>
          </div>
        </aside>

        {/* ── Main Content ── */}
        <section className="content-area">
          {renderPage()}
        </section>

      </div>
    </main>
  );
}
