'use client';

import { useEffect, useMemo, useState } from "react";
import {
  QueryFilters,
  fetchMe,
  generateReports,
  getDashboardStatus,
  loginAdmin,
  logoutAdmin,
  mediaUrl,
  uploadMonthlyDatasets,
  type DashboardStatus,
  type ReportResponse,
  type UploadResponse,
} from "../lib/api";

const STORAGE_KEY = "plantation_admin_token";

function formatNumber(value: number | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export default function AdminDashboard() {
  const [token, setToken] = useState("");
  const [username, setUsername] = useState("datainput");
  const [password, setPassword] = useState("data123");
  const [authLoading, setAuthLoading] = useState(true);
  const [loginBusy, setLoginBusy] = useState(false);

  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [outputMode, setOutputMode] = useState("region");
  const [uploadBusy, setUploadBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [reportResult, setReportResult] = useState<ReportResponse | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selectedMonth = uploadResult?.selected_month || status?.selected_month || "";

  async function refreshStatus() {
    try {
      const next = await getDashboardStatus();
      setStatus(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    async function boot() {
      const stored = window.localStorage.getItem(STORAGE_KEY) || "";
      if (!stored) {
        setAuthLoading(false);
        return;
      }

      try {
        await fetchMe(stored);
        setToken(stored);
        await refreshStatus();
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      } finally {
        setAuthLoading(false);
      }
    }

    boot();
  }, []);

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    setLoginBusy(true);
    setError("");
    try {
      const response = await loginAdmin(username, password);
      window.localStorage.setItem(STORAGE_KEY, response.token);
      setToken(response.token);
      setMessage("Admin login successful.");
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoginBusy(false);
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    try {
      if (token) {
        await logoutAdmin(token);
      }
    } catch {
      // ignore logout network issues
    }
    window.localStorage.removeItem(STORAGE_KEY);
    setToken("");
    setUploadResult(null);
    setReportResult(null);
    setMessage("");
  }

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (!files.length) {
      setError("Choose monthly Excel files first.");
      return;
    }

    setUploadBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await uploadMonthlyDatasets(token, files);
      setUploadResult(response);
      setMessage(response.message);
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploadBusy(false);
    }
  }

  async function handleGenerate() {
    if (!token || !selectedMonth) {
      setError("Upload or activate a monthly dataset before generating reports.");
      return;
    }

    setReportBusy(true);
    setError("");
    try {
      const response = await generateReports(token, selectedMonth, outputMode);
      setReportResult(response);
      setMessage(response.message);
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setReportBusy(false);
    }
  }

  const validationCards = useMemo(() => {
    return Object.entries(uploadResult?.validation || {});
  }, [uploadResult]);

  if (authLoading) {
    return <main className="pageShell"><section className="panelCard emptyPanel">Loading admin page...</section></main>;
  }

  if (!token) {
    return (
      <main className="pageShell narrowShell">
        <section className="heroCard adminHero">
          <div>
            <p className="eyebrow">Admin access</p>
            <h1 className="heroTitle">Data input dashboard</h1>
            <p className="heroText">
              This is the second page of the project. It keeps the monthly Excel input flow, removes
              OTP login, and uses backend-based username/password authentication.
            </p>
          </div>
          <a className="heroLink" href="/">
            Back to main dashboard
          </a>
        </section>

        <section className="panelCard adminLoginCard">
          <div className="sectionHeader">
            <div>
              <p className="eyebrow">Secure entry</p>
              <h2>Login to monthly data input</h2>
            </div>
          </div>

          <form className="adminForm" onSubmit={handleLogin}>
            <label className="field">
              <span>Username</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>

            <button className="btn btnPrimary fullWidth" disabled={loginBusy} type="submit">
              {loginBusy ? "Signing in..." : "Open admin dashboard"}
            </button>

            {error ? <pre className="errorText">{error}</pre> : null}
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="pageShell">
      <section className="heroCard adminHero">
        <div>
          <p className="eyebrow">Admin dashboard</p>
          <h1 className="heroTitle">Monthly data input and report control</h1>
          <p className="heroText">
            Upload the same flexible Excel format, validate region files, activate the month, and
            generate full Excel, PDF, and ZIP report outputs from one clean admin page.
          </p>
        </div>

        <div className="heroStats">
          <div className="heroStat">
            <span>Active month</span>
            <strong>{status?.selected_month || "—"}</strong>
          </div>
          <div className="heroStat">
            <span>Rows</span>
            <strong>{formatNumber(uploadResult?.dashboard_stats.row_count || status?.row_count)}</strong>
          </div>
          <div className="heroStat">
            <span>Regions</span>
            <strong>{status?.regions?.length || 0}</strong>
          </div>
          <div className="buttonRow">
            <a className="btn btnGhost" href="/">
              Main page
            </a>
            <button className="btn btnSecondary" onClick={handleLogout} type="button">
              Logout
            </button>
          </div>
        </div>
      </section>

      {message ? <section className="panelCard successText">{message}</section> : null}
      {error ? <section className="panelCard"><pre className="errorText">{error}</pre></section> : null}

      <section className="summaryGrid">
        <article className="panelCard">
          <div className="sectionHeader compact">
            <div>
              <p className="eyebrow">Dataset overview</p>
              <h2>{status?.month_label || "No active upload yet"}</h2>
            </div>
          </div>
          <div className="statGrid">
            <div className="statTile">
              <span>Plantations</span>
              <strong>{status?.plantations?.length || 0}</strong>
            </div>
            <div className="statTile">
              <span>Estates</span>
              <strong>{status?.estates?.length || 0}</strong>
            </div>
            <div className="statTile">
              <span>Divisions</span>
              <strong>{status?.divisions?.length || 0}</strong>
            </div>
            <div className="statTile">
              <span>Uploaded months</span>
              <strong>{status?.uploaded_months?.length || 0}</strong>
            </div>
          </div>
        </article>

        <article className="panelCard">
          <div className="sectionHeader compact">
            <div>
              <p className="eyebrow">Report package</p>
              <h2>{reportResult?.selected_month || status?.active_report?.selected_month || "Not generated yet"}</h2>
            </div>
          </div>
          <div className="buttonRow wrap">
            {status?.active_report?.downloads ? (
              <>
                <a className="btn btnGhost" href={mediaUrl(status.active_report.downloads.excel)} target="_blank" rel="noreferrer">
                  Excel
                </a>
                <a className="btn btnGhost" href={mediaUrl(status.active_report.downloads.pdf)} target="_blank" rel="noreferrer">
                  PDF
                </a>
                <a className="btn btnPrimary" href={mediaUrl(status.active_report.downloads.zip)} target="_blank" rel="noreferrer">
                  ZIP
                </a>
              </>
            ) : (
              <p className="softNote">Generate the report package after upload.</p>
            )}
          </div>
        </article>
      </section>

      <section className="panelCard">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Step 1</p>
            <h2>Upload monthly regional Excel files</h2>
          </div>
        </div>

        <form className="adminForm" onSubmit={handleUpload}>
          <label className="field">
            <span>Monthly files</span>
            <input
              multiple
              accept=".xlsx,.xls"
              type="file"
              onChange={(event) => setFiles(Array.from(event.target.files || []))}
            />
          </label>

          <div className="fileChipRow">
            {files.map((file) => (
              <span className="fileChip" key={file.name}>
                {file.name}
              </span>
            ))}
          </div>

          <button className="btn btnPrimary fullWidth" disabled={uploadBusy} type="submit">
            {uploadBusy ? "Uploading..." : "Upload and activate month"}
          </button>
        </form>
      </section>

      {!!validationCards.length && (
        <section className="panelCard">
          <div className="sectionHeader">
            <div>
              <p className="eyebrow">Validation results</p>
              <h2>Region-by-region upload check</h2>
            </div>
          </div>

          <div className="validationGrid">
            {validationCards.map(([region, item]) => (
              <article className="validationCard" key={region}>
                <div className="validationHeader">
                  <strong>{region}</strong>
                  <span>{item.row_count} rows</span>
                </div>
                <p className="softNote">{item.filename}</p>
                <p className="softNote">Detected month: {item.detected_month}</p>
                <p className="softNote">Mapped codes: {item.mapped_code_count ?? 0}</p>
                {item.missing_columns?.length ? (
                  <p className="errorInline">Missing: {item.missing_columns.join(", ")}</p>
                ) : (
                  <p className="successInline">Required columns passed</p>
                )}
                {item.region_issues?.length ? (
                  <p className="errorInline">Issues: {item.region_issues.join(", ")}</p>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="panelCard">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Step 2</p>
            <h2>Generate the final report package</h2>
          </div>
          <button className="btn btnPrimary" disabled={reportBusy} onClick={handleGenerate} type="button">
            {reportBusy ? "Generating..." : "Generate reports"}
          </button>
        </div>

        <div className="filterGrid">
          <label className="field">
            <span>Selected month</span>
            <input value={selectedMonth} readOnly />
          </label>

          <label className="field">
            <span>Output mode</span>
            <select value={outputMode} onChange={(event) => setOutputMode(event.target.value)}>
              <option value="region">Region</option>
              <option value="plantation">Plantation</option>
            </select>
          </label>
        </div>

        {reportResult?.downloads ? (
          <div className="buttonRow wrap">
            <a className="btn btnGhost" href={mediaUrl(reportResult.downloads.excel)} target="_blank" rel="noreferrer">
              Download Excel
            </a>
            <a className="btn btnGhost" href={mediaUrl(reportResult.downloads.pdf)} target="_blank" rel="noreferrer">
              Download PDF
            </a>
            <a className="btn btnPrimary" href={mediaUrl(reportResult.downloads.zip)} target="_blank" rel="noreferrer">
              Download ZIP
            </a>
          </div>
        ) : null}
      </section>

      {!!(reportResult?.preview_images?.length || 0) && (
        <section className="panelCard">
          <div className="sectionHeader">
            <div>
              <p className="eyebrow">Preview images</p>
              <h2>Generated report visuals</h2>
            </div>
          </div>

          <div className="previewGrid">
            {reportResult?.preview_images.map((image, index) => (
              <img className="previewImage" key={`${image}-${index}`} src={mediaUrl(image)} alt={`Report preview ${index + 1}`} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
