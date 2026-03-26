import { useState } from "react";

function InputForm({
  cashBalance,
  onCashBalance,
  onAddTransaction,
  onImportFile,
  onAnalyze,
}) {
  const [transactionType, setTransactionType] = useState("due_debit");
  const [vendor, setVendor] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [penaltyIfLate, setPenaltyIfLate] = useState("");
  const [flexibility, setFlexibility] = useState("medium");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [transactionMessage, setTransactionMessage] = useState("");

  const isDueTransaction =
    transactionType === "due_credit" || transactionType === "due_debit";
  const isDueDebit = transactionType === "due_debit";

  const getTodayDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const handleCashBalanceChange = (event) => {
    const value = event.target.value;
    onCashBalance(Number(value || 0));
  };

  const handleAddTransaction = (event) => {
    event.preventDefault();
    setTransactionMessage("");

    if (!amount || (isDueTransaction && !dueDate)) {
      setTransactionMessage("Enter amount and date for due transactions.");
      return;
    }

    const transaction = {
      id: `tx-${Date.now()}`,
      type: transactionType,
      amount: Number(amount),
      date: isDueTransaction ? dueDate : getTodayDate(),
      vendor: vendor || undefined,
    };

    if (isDueDebit) {
      transaction.penalty_if_late = Number(penaltyIfLate || 0);
      transaction.flexibility = flexibility;
    }

    const outcome = onAddTransaction(transaction);
    if (!outcome?.ok) {
      setTransactionMessage(outcome?.error || "Transaction could not be added.");
      return;
    }

    setVendor("");
    setAmount("");
    setDueDate("");
    setPenaltyIfLate("");
    setFlexibility("medium");
    setTransactionMessage("Transaction added.");
  };

  const handleImportDocument = async () => {
    if (!uploadFile || !onImportFile) {
      return;
    }

    setUploadMessage("Importing file...");
    try {
      const importedCount = await onImportFile(uploadFile);
      setUploadMessage(
        `Imported ${importedCount} item(s) from ${uploadFile.name}.`,
      );
      setUploadFile(null);
    } catch (error) {
      setUploadMessage(error?.message || "Failed to import file.");
    }
  };

  return (
    <section className="panel">
      <h2 className="panel-title">Input Financial Data</h2>

      <div className="upload-row">
        <input
          type="file"
          accept=".csv,.pdf,image/png,image/jpeg,image/jpg,image/webp"
          onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
          className="field-input"
        />
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleImportDocument}
          disabled={!uploadFile}
        >
          Import CSV/PDF/Image
        </button>
      </div>
      {uploadMessage && <p className="helper-text">{uploadMessage}</p>}
      {transactionMessage && <p className="helper-text">{transactionMessage}</p>}

      <div className="cash-field">
        <label className="field-label">
          Cash Balance
          <input
            type="number"
            value={cashBalance}
            onChange={handleCashBalanceChange}
            className="field-input"
            placeholder="230000"
            min="0"
            step="0.01"
          />
        </label>
      </div>

      <form onSubmit={handleAddTransaction} className="obligation-grid">
        <label className="field-label">
          Transaction Type
          <select
            value={transactionType}
            onChange={(event) => {
              const nextType = event.target.value;
              setTransactionType(nextType);
              if (nextType === "immediate_credit" || nextType === "immediate_debit") {
                setDueDate("");
              }
            }}
            className="field-input field-select"
          >
            <option value="immediate_credit">Immediate credit</option>
            <option value="immediate_debit">Immediate debit</option>
            <option value="due_credit">Due credit</option>
            <option value="due_debit">Due debit</option>
          </select>
        </label>
        <input
          value={vendor}
          onChange={(event) => setVendor(event.target.value)}
          className="field-input"
          placeholder="Vendor"
        />
        <input
          type="number"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          className="field-input"
          placeholder="Amount"
          min="0.01"
          step="0.01"
          required
        />
        {isDueTransaction ? (
          <input
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
            className="field-input"
            required
          />
        ) : (
          <input
            type="text"
            value={getTodayDate()}
            className="field-input"
            disabled
            readOnly
            aria-label="Date auto-set to today for immediate transaction"
          />
        )}
        <input
          type="number"
          value={penaltyIfLate}
          onChange={(event) => setPenaltyIfLate(event.target.value)}
          className="field-input"
          placeholder="Penalty if late"
          min="0"
          step="0.01"
          disabled={!isDueDebit}
        />
        <label className="field-label">
          Flexibility
          <select
            value={flexibility}
            onChange={(event) => setFlexibility(event.target.value)}
            className="field-input field-select"
            disabled={!isDueDebit}
          >
            <option value="low">Low flexibility</option>
            <option value="medium">Medium flexibility</option>
            <option value="high">High flexibility</option>
          </select>
        </label>

        <div className="button-row">
          <button type="submit" className="btn btn-primary">
            Add Transaction
          </button>

          <button
            type="button"
            onClick={onAnalyze}
            className="btn btn-secondary"
          >
            Analyze
          </button>
        </div>
      </form>
    </section>
  );
}

export default InputForm;
