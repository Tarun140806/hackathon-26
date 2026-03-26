import { useState, useEffect } from "react";
import { exportPDF, updatePaymentStatus, getPaymentTrackingSummary, storeAnalysis, recalculateAnalysis } from "../api";

function Results({ analysisResult, onAnalysisUpdate }) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(null);
  const [paymentStatuses, setPaymentStatuses] = useState({});
  const [paymentTrackingSummary, setPaymentTrackingSummary] = useState(null);
  const [recalculatedAnalysis, setRecalculatedAnalysis] = useState(null);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [whatIfAmount, setWhatIfAmount] = useState("");

  // Store analysis when it loads
  useEffect(() => {
    if (analysisResult && analysisResult.prioritized_obligations) {
      // Ensure all obligations have IDs
      const obligationsWithIds = analysisResult.prioritized_obligations.map((ob, index) => {
        if (!ob.id) {
          ob.id = `${(ob.vendor || "obligation").replace(/\s+/g, "-").toLowerCase()}-${index}`;
        }
        return ob;
      });

      storeAnalysis({
        cash_balance: analysisResult.cash_balance,
        prioritized_obligations: obligationsWithIds,
      }).catch(err => console.log("Note: Could not store analysis state", err));
      
      // Load payment statuses for all obligations
      const loadPaymentStatuses = async () => {
        try {
          const statuses = {};
          for (const ob of obligationsWithIds) {
            const status = await fetch(`http://localhost:8000/features/payment-status/${ob.id}`)
              .then(r => r.json())
              .catch(() => ({ status: "pending" }));
            statuses[ob.id] = status.status || "pending";
          }
          setPaymentStatuses(statuses);
        } catch (err) {
          console.log("Could not load payment statuses", err);
        }
      };
      loadPaymentStatuses();
    }
  }, [analysisResult]);

  const formatCurrency = (value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return "-";
    }
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(numeric);
  };

  const handleExportPDF = async () => {
    setIsExporting(true);
    setExportError(null);
    try {
      const pdfData = {
        cash_balance: analysisResult.cash_balance,
        total_obligations: analysisResult.total_obligations,
        shortfall: analysisResult.shortfall,
        prioritized_obligations: analysisResult.prioritized_obligations || [],
        reasoning: analysisResult.reasoning || "",
        email_draft: analysisResult.email_draft || "",
        chain_reaction: analysisResult.chain_reaction || "",
      };

      const response = await exportPDF(pdfData);
      
      if (response.pdf_base64) {
        // Decode base64 and create blob
        const binaryString = atob(response.pdf_base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: "application/pdf" });

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = response.filename || "cashclear_analysis.pdf";
        link.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      setExportError(`Export failed: ${error.message}`);
      console.error("PDF export error:", error);
    } finally {
      setIsExporting(false);
    }
  };

  const handlePaymentStatusChange = async (obligationId, newStatus) => {
    try {
      await updatePaymentStatus(obligationId, newStatus, new Date().toISOString().split('T')[0], "");
      setPaymentStatuses({
        ...paymentStatuses,
        [obligationId]: newStatus,
      });
      
      // Fetch updated summary
      const summary = await getPaymentTrackingSummary();
      setPaymentTrackingSummary(summary);

      // Recalculate analysis whenever payment status changes
      const updated = await recalculateAnalysis();
      setRecalculatedAnalysis(updated);
      
      // Sync payment statuses from obligations list if available
      if (updated.remaining_obligations_list) {
        const newStatuses = { ...paymentStatuses };
        for (const ob of analysisResult.prioritized_obligations || []) {
          const isPaid = !updated.remaining_obligations_list.some(r => r.id === ob.id);
          if (isPaid) {
            newStatuses[ob.id] = "paid";
          }
        }
        setPaymentStatuses(newStatuses);
      }
    } catch (error) {
      console.error("Failed to update payment status:", error);
    }
  };

  const handleLoadPaymentSummary = async () => {
    try {
      const summary = await getPaymentTrackingSummary();
      setPaymentTrackingSummary(summary);
      
      // Also trigger recalculation to sync UI
      const updated = await recalculateAnalysis();
      setRecalculatedAnalysis(updated);
      
      console.log("Payment summary loaded:", summary);
    } catch (error) {
      console.error("Failed to load payment summary:", error);
    }
  };

  if (!analysisResult) {
    return (
      <section className="panel">
        <p className="empty-text">No results yet</p>
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
    email_draft,
    chain_reaction,
  } = analysisResult;

  // Calculate current shortfall based on payments
  const currentShortfall = recalculatedAnalysis ? recalculatedAnalysis.new_shortfall : shortfall;

  return (
    <section className="panel results-panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 className="panel-title">Analysis Results</h2>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={handleExportPDF}
            disabled={isExporting}
            style={{
              padding: "8px 16px",
              backgroundColor: "#10b981",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: isExporting ? "not-allowed" : "pointer",
              fontSize: "14px",
              fontWeight: "500",
            }}
          >
            {isExporting ? "Generating..." : "📥 Download PDF"}
          </button>
          <button
            onClick={handleLoadPaymentSummary}
            style={{
              padding: "8px 16px",
              backgroundColor: "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: "500",
            }}
          >
            📊 Track Payments
          </button>
        </div>
      </div>

      {exportError && (
        <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px", marginBottom: "16px" }}>
          {exportError}
        </div>
      )}

      {paymentTrackingSummary && (
        <div style={{ backgroundColor: "#f0fdf4", padding: "12px", borderRadius: "6px", marginBottom: "16px" }}>
          <p style={{ fontWeight: "bold", marginBottom: "8px" }}>Payment Tracking Summary</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px", fontSize: "12px" }}>
            <div>✓ Paid: {paymentTrackingSummary.paid}</div>
            <div>📅 Scheduled: {paymentTrackingSummary.scheduled}</div>
            <div>⏳ Pending: {paymentTrackingSummary.pending}</div>
            <div>⚠️ Overdue: {paymentTrackingSummary.overdue}</div>
          </div>
          <p style={{ marginTop: "8px" }}>Payment Rate: {paymentTrackingSummary.payment_rate}</p>
        </div>
      )}

      <div className="summary-grid">
        <div className="summary-card">
          <p className="summary-label">Cash Balance</p>
          <p className="summary-value">{formatCurrency(cash_balance)}</p>
        </div>
        <div className="summary-card">
          <p className="summary-label">Total Obligations</p>
          <p className="summary-value">{formatCurrency(total_obligations)}</p>
        </div>
        <div className="summary-card">
          <p className="summary-label">Shortfall</p>
          <p className="summary-value" style={{ color: currentShortfall > 0 ? "#dc2626" : "#059669" }}>
            {formatCurrency(currentShortfall)}
          </p>
        </div>
        <div className="summary-card">
          <p className="summary-label">Days to Zero</p>
          <p className="summary-value">{days_to_zero ?? "-"}</p>
        </div>
      </div>

      <div>
        <h3 className="section-title">Prioritized Obligations</h3>
        {prioritized_obligations.length === 0 ? (
          <p className="empty-text">No results yet</p>
        ) : (
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Score</th>
                  <th>Can Pay</th>
                  <th>Risk Level</th>
                  <th>Payment Status</th>
                </tr>
              </thead>
              <tbody>
                {prioritized_obligations.map((item) => {
                  const isPaid = paymentStatuses[item.id] === "paid";
                  return (
                    <tr
                      key={item.id || `${item.vendor}-${item.amount}`}
                      className={`row-risk-${item.risk_level || "unknown"}`}
                      style={{
                        opacity: isPaid ? 0.6 : 1,
                        backgroundColor: isPaid ? "#f0fdf4" : "transparent",
                      }}
                    >
                      <td style={{ textDecoration: isPaid ? "line-through" : "none" }}>
                        {item.vendor || "-"} {isPaid && "✓"}
                      </td>
                      <td style={{ textDecoration: isPaid ? "line-through" : "none" }}>
                        {formatCurrency(item.amount)}
                      </td>
                      <td>{item.score ?? "-"}</td>
                      <td>{item.can_pay ? "✓ Yes" : "✗ No"}</td>
                      <td>
                        <span
                          className={`risk-pill risk-${item.risk_level || "unknown"}`}
                        >
                          {item.risk_level || "-"}
                        </span>
                      </td>
                      <td>
                        <select
                          value={paymentStatuses[item.id] || "pending"}
                          onChange={(e) =>
                            handlePaymentStatusChange(item.id, e.target.value)
                          }
                          style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            border: isPaid ? "2px solid #059669" : "1px solid #d1d5db",
                            fontSize: "12px",
                            cursor: "pointer",
                            fontWeight: isPaid ? "bold" : "normal",
                          }}
                        >
                          <option value="pending">Pending</option>
                          <option value="scheduled">Scheduled</option>
                          <option value="paid">✓ Paid</option>
                          <option value="overdue">Overdue</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="reasoning-card">
        <h3 className="section-title">Financial Analysis & Reasoning</h3>
        <p className="reasoning-text">{reasoning || "No results yet"}</p>
      </div>

      {email_draft && (
        <div className="reasoning-card">
          <h3 className="section-title">📧 Recommended Payment Communication</h3>
          <p className="reasoning-text">{email_draft}</p>
        </div>
      )}

      {chain_reaction && (
        <div className="reasoning-card">
          <h3 className="section-title">⛓️ Chain-Reaction Impact Analysis</h3>
          <p className="reasoning-text">{chain_reaction}</p>
        </div>
      )}

      <div style={{ marginTop: "20px", padding: "16px", backgroundColor: "#f3f4f6", borderRadius: "6px" }}>
        <h3 className="section-title">🎯 What-If Scenarios</h3>
        <p style={{ fontSize: "12px", marginBottom: "12px" }}>Simulate cash position changes</p>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <input
            type="number"
            value={whatIfAmount}
            onChange={(e) => setWhatIfAmount(e.target.value)}
            placeholder="Amount (e.g., 50000 for +INR50k)"
            style={{
              flex: 1,
              padding: "8px",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          />
          <button
            onClick={() => {
              if (whatIfAmount) {
                console.log(`What-if scenario: ${whatIfAmount}`);
                setWhatIfAmount("");
              }
            }}
            style={{
              padding: "8px 16px",
              backgroundColor: "#7c3aed",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: "500",
            }}
          >
            Analyze
          </button>
        </div>
      </div>
    </section>
  );
}

export default Results;
