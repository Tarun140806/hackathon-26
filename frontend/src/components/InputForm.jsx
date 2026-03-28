import { useState } from "react";

function InputForm({
  cashBalance,
  onCashBalance,
  onAddObligation,
  onImportFile,
  onAnalyze,
}) {
  const [vendor, setVendor] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [penaltyIfLate, setPenaltyIfLate] = useState("");
  const [flexibility, setFlexibility] = useState("medium");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const handleCashBalanceChange = (e) => {
    onCashBalance(Number(e.target.value || 0));
  };

  const handleAddObligation = (e) => {
    e.preventDefault();
    if (!vendor || !amount || !dueDate) return;

    onAddObligation({
      id: `ob-${Date.now()}`,
      vendor,
      amount: Number(amount),
      due_date: dueDate,
      penalty_if_late: Number(penaltyIfLate || 0),
      flexibility,
    });

    setVendor("");
    setAmount("");
    setDueDate("");
    setPenaltyIfLate("");
    setFlexibility("medium");
  };

  const handleImportDocument = async () => {
    if (!uploadFile || !onImportFile) return;
    setUploadMessage("Importing…");
    setUploadError("");
    try {
      const count = await onImportFile(uploadFile);
      setUploadMessage(`✓ Imported ${count} obligation(s) from "${uploadFile.name}".`);
      setUploadFile(null);
    } catch (err) {
      setUploadError(err?.message || "Failed to import file.");
      setUploadMessage("");
    }
  };

  return (
    <div className="panel">
      {/* Panel header */}
      <div className="panel-header">
        <h2 className="panel-title">
          <span className="panel-title-icon">📥</span>
          Input Financial Data
        </h2>
      </div>

      {/* ── Upload section ── */}
      <div className="upload-zone">
        <input
          id="file-upload"
          type="file"
          accept=".csv,.pdf,image/png,image/jpeg,image/jpg,image/webp"
          onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
          className="field-input"
        />
        <button
          id="import-btn"
          type="button"
          className="btn btn-secondary"
          onClick={handleImportDocument}
          disabled={!uploadFile}
        >
          Import
        </button>
        <p className="upload-hint">
          📎 Accepts CSV, PDF, PNG, JPG, WEBP
        </p>
      </div>

      {uploadMessage && (
        <p className="helper-text">{uploadMessage}</p>
      )}
      {uploadError && (
        <p className="state-block state-error" style={{ marginBottom: "14px" }}>
          ⚠ {uploadError}
        </p>
      )}

      {/* ── Cash balance ── */}
      <div className="field-group">
        <label htmlFor="cash-balance" className="field-label">
          Cash Balance (₹)
        </label>
        <input
          id="cash-balance"
          type="number"
          value={cashBalance}
          onChange={handleCashBalanceChange}
          className="field-input"
          placeholder="e.g. 2,30,000"
          min="0"
        />
      </div>

      <div className="divider" />

      {/* ── Add Obligation form ── */}
      <p className="field-label" style={{ marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
        <span>➕</span> Add Obligation
      </p>

      <form onSubmit={handleAddObligation} className="obligation-grid">
        <div className="field-group">
          <label className="field-label" htmlFor="ob-vendor">Vendor</label>
          <input
            id="ob-vendor"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            className="field-input"
            placeholder="e.g. Supplier Co."
            required
          />
        </div>

        <div className="field-group">
          <label className="field-label" htmlFor="ob-amount">Amount (₹)</label>
          <input
            id="ob-amount"
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="field-input"
            placeholder="e.g. 50000"
            min="0"
            required
          />
        </div>

        <div className="field-group">
          <label className="field-label" htmlFor="ob-due">Due Date</label>
          <input
            id="ob-due"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="field-input"
            required
          />
        </div>

        <div className="field-group">
          <label className="field-label" htmlFor="ob-penalty">Penalty if Late (₹)</label>
          <input
            id="ob-penalty"
            type="number"
            value={penaltyIfLate}
            onChange={(e) => setPenaltyIfLate(e.target.value)}
            className="field-input"
            placeholder="e.g. 2000"
            min="0"
          />
        </div>

        <div className="field-group full-width">
          <label className="field-label" htmlFor="ob-flex">Payment Flexibility</label>
          <select
            id="ob-flex"
            value={flexibility}
            onChange={(e) => setFlexibility(e.target.value)}
            className="field-input"
          >
            <option value="low">Low — must pay on time</option>
            <option value="medium">Medium — some room</option>
            <option value="high">High — can defer</option>
          </select>
        </div>

        <div className="button-row">
          <button id="add-obligation-btn" type="submit" className="btn btn-primary">
            + Add Obligation
          </button>
          <button
            id="analyze-btn"
            type="button"
            onClick={onAnalyze}
            className="btn btn-cta"
          >
            ⚡ Analyze Now
          </button>
        </div>
      </form>
    </div>
  );
}

export default InputForm;
