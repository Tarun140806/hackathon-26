function Results({ analysisResult }) {
  const formatCurrency = (value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "—";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(numeric);
  };

  if (!analysisResult) {
    return (
      <section className="panel">
        <p className="empty-text">No results yet. Add obligations and click Analyze.</p>
      </section>
    );
  }

  const {
    cash_balance,
    total_obligations,
    shortfall,
    days_to_zero,
    prioritized_obligations = [],
    reasoning,
  } = analysisResult;

  const SUMMARY_CARDS = [
    { label: "Cash Balance",      value: formatCurrency(cash_balance),      icon: "💰" },
    { label: "Total Obligations", value: formatCurrency(total_obligations),  icon: "📋" },
    { label: "Shortfall",         value: formatCurrency(shortfall),          icon: "⚠️" },
    { label: "Days to Zero",      value: days_to_zero ?? "—",               icon: "📅" },
  ];

  return (
    <section className="panel results-panel">
      {/* Header */}
      <div className="panel-header">
        <h2 className="panel-title">
          <span className="panel-title-icon">📊</span>
          Analysis Results
        </h2>
      </div>

      {/* ── Summary Cards ── */}
      <div className="summary-grid">
        {SUMMARY_CARDS.map(({ label, value, icon }) => (
          <div key={label} className="summary-card">
            <p className="summary-label">{icon} {label}</p>
            <p className="summary-value">{value}</p>
          </div>
        ))}
      </div>

      <div className="divider" />

      {/* ── Prioritized Obligations Table ── */}
      <div>
        <div className="section-header">
          <h3 className="section-title">
            🗂 Prioritized Obligations
          </h3>
          {prioritized_obligations.length > 0 && (
            <span className="section-count">{prioritized_obligations.length} items</span>
          )}
        </div>

        {prioritized_obligations.length === 0 ? (
          <p className="empty-text">No obligations to display.</p>
        ) : (
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Score</th>
                  <th>Can Pay</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {prioritized_obligations.map((item, idx) => (
                  <tr
                    key={item.id || `${item.vendor}-${item.amount}-${idx}`}
                    className={`row-risk-${item.risk_level || "unknown"}`}
                  >
                    <td style={{ color: "var(--text-dim)", width: 36 }}>{idx + 1}</td>
                    <td style={{ fontWeight: 600 }}>{item.vendor || "—"}</td>
                    <td>{formatCurrency(item.amount)}</td>
                    <td>
                      <span style={{
                        fontFamily: "'Space Grotesk', sans-serif",
                        fontWeight: 700,
                        color: "var(--accent-2)",
                      }}>
                        {item.score ?? "—"}
                      </span>
                    </td>
                    <td>
                      <span className={item.can_pay ? "pay-yes" : "pay-no"}>
                        {item.can_pay ? "✓ Yes" : "✗ No"}
                      </span>
                    </td>
                    <td>
                      <span className={`risk-pill risk-${item.risk_level || "unknown"}`}>
                        {item.risk_level || "unknown"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="divider" />

      {/* ── AI Reasoning ── */}
      <div>
        <h3 className="section-title" style={{ marginBottom: 12 }}>
          🤖 AI Reasoning
        </h3>
        <div className="reasoning-card">
          <p className="reasoning-text">{reasoning || "No reasoning returned."}</p>
        </div>
      </div>
    </section>
  );
}

export default Results;
