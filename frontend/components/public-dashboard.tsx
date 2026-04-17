"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  QueryFilters,
  QueryResponse,
  QueryRow,
  buildExportCsvUrl,
  getDashboardOptions,
  getDashboardStatus,
  getEstateSummary,
  getRegionSummary,
  mediaUrl,
  runDashboardQuery,
  type AccessScope,
  type DashboardStatus,
  type EstateSummary,
  type FilterOptions,
  type RegionSummary,
} from "../lib/api";
import { getExternalScopeIdentity, persistExternalScopeIdentity } from "../lib/auth-scope";

const defaultFilters: QueryFilters = {
  plantation: "",
  region: "",
  estate: "",
  division: "",
  year: "",
  metric: "Division_Yield",
  operator: "",
  value: "",
  rankDir: "",
  count: "10",
  benchmarkMetric: "",
};

const plantationChoices = [
  { label: "All Accessible Plantations", value: "HAYLEYS", image: "/plantations/hayleys.png" },
  { label: "Talawakelle Tea Estates", value: "TTEL", image: "/plantations/ttel.png" },
  { label: "Kelani Valley Plantations", value: "KVPL", image: "/plantations/kvpl.png" },
  { label: "Horana Plantations", value: "HPL", image: "/plantations/hpl.png" },
] as const;

const plantationDisplayNames: Record<string, string> = {
  HAYLEYS: "All Accessible Plantations",
  TTEL: "Talawakelle Tea Estates",
  KVPL: "Kelani Valley Plantations",
  HPL: "Horana Plantations",
};

const regionDisplayNames: Record<string, string> = {
  TK: "Talawakelle Region",
  NO: "Nanu Oya Region",
  TTEL_LC: "Talawakelle Low Country Region",
  NE: "Nuwara Eliya",
  HT: "Hatton",
  KVPL_LC: "Kelani Valley Low Country - Tea",
  UC: "UPCOT",
  LD: "Lindula",
  HPL_LC: "Horana Low Country - Tea",
};

const yearDisplayNames: Record<string, string> = {
  First_Year: "1st Year",
  Second_Year: "2nd Year",
  Third_Year: "3rd Year",
  Fourth_Year: "4th Year",
  Fifth_Year: "5th Year",
  VP: "VP",
  SD: "SD",
  "VP & SD": "VP & SD",
};

const chartYearTokens: Record<string, string[]> = {
  First_Year: ["1st year", "first year", "1-12 months", "graph 1"],
  Second_Year: ["2nd year", "second year", "13-24 months", "graph 2"],
  Third_Year: ["3rd year", "third year", "25-36 months", "graph 3"],
  Fourth_Year: ["4th year", "fourth year", "37-48 months", "graph 4"],
  Fifth_Year: ["5th year", "fifth year", "48+ months", "graph 5"],
  VP: ["vp yield", "graph vp", " vp "],
  SD: ["sd yield", "graph sd", " sd "],
  "VP & SD": ["total", "vp + sd", "vp & sd", "graph tot"],
};

type ModeKey = "" | "top" | "bottom" | "above" | "below";
type ViewerMode = "" | "charts" | "maps";

function formatNumber(value: number | undefined, digits = 0) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function normalizeText(value: string) {
  return ` ${String(value || "").toLowerCase().replace(/[_-]+/g, " ")} `;
}

function prettyYearLabel(value: string) {
  return yearDisplayNames[value] || value.replace(/_/g, " ");
}

function chartTitleMatchesYear(title: string, year: string) {
  if (!year) return true;
  const cleanTitle = normalizeText(title);
  const tokens = chartYearTokens[year] || [];
  return tokens.some((token) => cleanTitle.includes(normalizeText(token)));
}

function simplifyChartTitle(title: string) {
  const cleanTitle = String(title || "").trim();
  if (!cleanTitle) return "Chart";
  const found = Object.entries(chartYearTokens).find(([, tokens]) =>
    tokens.some((token) => normalizeText(cleanTitle).includes(normalizeText(token)))
  );
  if (found) return prettyYearLabel(found[0]);
  return cleanTitle
    .replace(/tea\s*-\s*vp\s*yph\s*-\s*/i, "")
    .replace(/divisional yield\s*-\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function plantationChoiceFromValue(value: string) {
  return value === "TTEL" || value === "KVPL" || value === "HPL" ? value : "HAYLEYS";
}

function allowedPlantationChoices(access: AccessScope | null) {
  const accessible = Array.from(new Set(access?.accessible_plantations || []));
  const role = access?.role || "";
  const allowGlobal = role === "md" || role === "admin";

  return plantationChoices.filter((choice) => {
    if (choice.value === "HAYLEYS") {
      return allowGlobal || accessible.length > 0;
    }
    if (allowGlobal) return true;
    return accessible.includes(choice.value);
  });
}


function displayPlantation(value: string) {
  return plantationDisplayNames[value] || value || "—";
}

function displayRegion(value: string) {
  return regionDisplayNames[value] || value || "—";
}

function getMode(filters: QueryFilters): ModeKey {
  if (filters.rankDir === "top") return "top";
  if (filters.rankDir === "bottom") return "bottom";
  if (filters.operator === ">") return "above";
  if (filters.operator === "<") return "below";
  return "";
}

function uniqueBy<T>(items: T[]) {
  return Array.from(new Set(items));
}

function buildMapLink(query: string) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

function buildMapEmbedUrl(query: string) {
  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;
}

function matchesFilterValue(current: string | undefined, expected: string) {
  if (!expected) return true;
  return (current || "").toLowerCase() === expected.toLowerCase();
}

function rowKey(row: QueryRow) {
  return `${row.plantation}|${row.region}|${row.estate}|${row.division}|${row.code}|${row.year}`;
}

export default function PublicDashboard() {
  const initialIdentity = useMemo(() => getExternalScopeIdentity(), []);
  const [authUsername] = useState<string | null>(initialIdentity.username);
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [access, setAccess] = useState<AccessScope | null>(null);
  const [filters, setFilters] = useState<QueryFilters>(defaultFilters);
  const [plantationChoice, setPlantationChoice] = useState<string>("HAYLEYS");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [regionSummary, setRegionSummary] = useState<RegionSummary | null>(null);
  const [estateSummary, setEstateSummary] = useState<EstateSummary | null>(null);
  const [focusedRow, setFocusedRow] = useState<QueryRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [viewerMode, setViewerMode] = useState<ViewerMode>("");
  const [error, setError] = useState("");
  const viewerSectionRef = useRef<HTMLElement | null>(null);
  const querySequenceRef = useRef(0);

  async function hydrateSummaries(nextFilters: QueryFilters, localOptions?: FilterOptions | null) {
    const sourceOptions = localOptions || options;
    const summaryRequests: Promise<void>[] = [];

    if (nextFilters.region && nextFilters.year) {
      summaryRequests.push(
        getRegionSummary({ region: nextFilters.region, year: nextFilters.year })
          .then(setRegionSummary)
          .catch(() => setRegionSummary(null))
      );
    } else if (nextFilters.estate && nextFilters.year) {
      const estateRegion =
        sourceOptions?.divisions.find((item) => item.estate === nextFilters.estate)?.region || "";
      if (estateRegion) {
        summaryRequests.push(
          getRegionSummary({ region: estateRegion, year: nextFilters.year })
            .then(setRegionSummary)
            .catch(() => setRegionSummary(null))
        );
      } else {
        setRegionSummary(null);
      }
    } else {
      setRegionSummary(null);
    }

    const derivedPlantation =
      nextFilters.plantation ||
      sourceOptions?.divisions.find((item) => {
        if (item.estate !== nextFilters.estate) return false;
        if (nextFilters.region && item.region !== nextFilters.region) return false;
        return true;
      })?.plantation ||
      "";

    if (derivedPlantation && nextFilters.estate && nextFilters.year) {
      summaryRequests.push(
        getEstateSummary({
          plantation: derivedPlantation,
          estate: nextFilters.estate,
          year: nextFilters.year,
        })
          .then(setEstateSummary)
          .catch(() => setEstateSummary(null))
      );
    } else {
      setEstateSummary(null);
    }

    await Promise.all(summaryRequests);
  }

  async function executeQuery(nextFilters = filters) {
    const requestId = ++querySequenceRef.current;
    setRunning(true);
    setError("");

    try {
      const nextResult = await runDashboardQuery(nextFilters);
      if (requestId !== querySequenceRef.current) return;
      setResult(nextResult);
      if (nextResult.access) {
        setAccess(nextResult.access);
      }
      await hydrateSummaries(nextFilters);
    } catch (err) {
      if (requestId !== querySequenceRef.current) return;
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      if (requestId === querySequenceRef.current) {
        setRunning(false);
      }
    }
  }

  async function boot() {
    try {
      persistExternalScopeIdentity();

      const identity = getExternalScopeIdentity();
      if (!identity.username) {
        setError("Open this dashboard through the central login page first.");
        return;
      }

      const [statusResponse, optionsResponse] = await Promise.all([
        getDashboardStatus(),
        getDashboardOptions(),
      ]);

      setStatus(statusResponse);
      setOptions(optionsResponse.options);
      setAccess(optionsResponse.access || statusResponse.access || null);

      const allowedChoices = allowedPlantationChoices(optionsResponse.access || statusResponse.access || null);
      const defaultPlantation =
        optionsResponse.access?.resolved_estate
          ? optionsResponse.access.accessible_plantations[0] || ""
          : allowedChoices.some((item) => item.value === "HAYLEYS")
            ? ""
            : allowedChoices[0]?.value || "";

      const firstMetric = optionsResponse.options.metrics[0]?.value || "Division_Yield";
      const initialFilters: QueryFilters = {
        ...defaultFilters,
        plantation: defaultPlantation,
        estate: optionsResponse.access?.resolved_estate || "",
        year: optionsResponse.options.years[0] || "",
        metric: firstMetric,
      };

      setFilters(initialFilters);
      setPlantationChoice(defaultPlantation ? plantationChoiceFromValue(defaultPlantation) : "HAYLEYS");

      const nextResult = await runDashboardQuery(initialFilters);
      setResult(nextResult);
      setAccess(nextResult.access || optionsResponse.access || statusResponse.access || null);
      await hydrateSummaries(initialFilters, optionsResponse.options);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void boot();
  }, []);

  useEffect(() => {
    if (!options || loading) return;
    void hydrateSummaries(filters, options);
  }, [filters.region, filters.estate, filters.year, filters.plantation, options, loading]);

  useEffect(() => {
    if (!options || loading) return;
    void executeQuery(filters);
  }, [filters, options, loading]);

  const filteredDivisionRows = useMemo(() => {
    if (!options?.divisions) return [];

    return options.divisions.filter((item) => {
      if (filters.plantation && item.plantation !== filters.plantation) return false;
      if (filters.region && item.region !== filters.region) return false;
      if (filters.estate && item.estate !== filters.estate) return false;
      return true;
    });
  }, [options, filters.plantation, filters.region, filters.estate]);

  const filteredRegions = useMemo(() => uniqueBy(filteredDivisionRows.map((item) => item.region)).sort(), [filteredDivisionRows]);

  const filteredEstates = useMemo(() => uniqueBy(filteredDivisionRows.map((item) => item.estate)).sort(), [filteredDivisionRows]);

  const derivedPlantation = useMemo(() => {
    if (focusedRow?.plantation) return focusedRow.plantation;
    if (filters.plantation) return filters.plantation;
    if (!options?.divisions) return "";
    if (filters.region) {
      return options.divisions.find((item) => item.region === filters.region)?.plantation || "";
    }
    if (filters.estate) {
      return options.divisions.find((item) => item.estate === filters.estate)?.plantation || "";
    }
    return "";
  }, [focusedRow, filters.plantation, filters.region, filters.estate, options]);

  const derivedRegion = useMemo(() => {
    if (focusedRow?.region) return focusedRow.region;
    if (filters.region) return filters.region;
    if (!options?.divisions || !filters.estate) return "";
    return options.divisions.find((item) => item.estate === filters.estate)?.region || "";
  }, [focusedRow, filters.region, filters.estate, options]);

  const activeMode = getMode(filters);
  const effectiveMetric = filters.benchmarkMetric || filters.metric || "Division_Yield";
  const parsedThreshold = Number(filters.value);

  const displayRows = useMemo(() => {
    let rows = [...(result?.rows || [])];

    rows = rows.filter((row) => {
      if (!matchesFilterValue(row.plantation, filters.plantation)) return false;
      if (!matchesFilterValue(row.region, filters.region)) return false;
      if (!matchesFilterValue(row.estate, filters.estate)) return false;
      if (!matchesFilterValue(row.year, filters.year)) return false;
      return true;
    });

    if ((activeMode === "above" || activeMode === "below") && Number.isFinite(parsedThreshold)) {
      rows = rows.filter((row) =>
        activeMode === "above"
          ? Number(row.value || 0) > parsedThreshold
          : Number(row.value || 0) < parsedThreshold
      );
    }

    if (activeMode === "top" || activeMode === "bottom") {
      const sorted = [...rows].sort((a, b) =>
        activeMode === "top"
          ? Number(b.value || 0) - Number(a.value || 0)
          : Number(a.value || 0) - Number(b.value || 0)
      );
      const take = Math.max(Number(filters.count || "10"), 1);
      rows = sorted.slice(0, take);
    }

    return rows;
  }, [result, filters, activeMode, parsedThreshold]);

  useEffect(() => {
    if (!focusedRow) return;
    const exists = displayRows.some((row) => rowKey(row) === rowKey(focusedRow));
    if (!exists) {
      setFocusedRow(null);
    }
  }, [displayRows, focusedRow]);

  const showSummaries = Boolean((filters.region && regionSummary) || (filters.estate && estateSummary));

  const contextYear = focusedRow?.year || filters.year;

  const reportChartGroups = useMemo(() => {
    const rawGroups =
      status?.active_report?.region_outputs ||
      (Array.isArray(status?.active_report?.regions) &&
      typeof status?.active_report?.regions?.[0] === "object"
        ? (status?.active_report?.regions as unknown as {
            region: string;
            assets: { title: string; kind: string; png: string; jpg: string; svg: string; page_png: string }[];
          }[])
        : []);

    if (!rawGroups?.length) return [];

    let allowedRegions: string[] = [];

    if (focusedRow?.region) {
      allowedRegions = [focusedRow.region];
    } else if (derivedRegion) {
      allowedRegions = [derivedRegion];
    } else if (derivedPlantation) {
      allowedRegions = uniqueBy(
        (options?.divisions || [])
          .filter((item) => item.plantation === derivedPlantation)
          .map((item) => item.region)
      );
    }

    return rawGroups
      .filter((group) => !allowedRegions.length || allowedRegions.includes(group.region))
      .map((group) => ({
        region: group.region,
        regionLabel: displayRegion(group.region),
        assets: (group.assets || [])
          .filter((asset) => asset.kind === "chart")
          .filter((asset) => chartTitleMatchesYear(asset.title, contextYear))
          .map((asset) => ({
            ...asset,
            cleanTitle: simplifyChartTitle(asset.title),
          })),
      }))
      .filter((group) => group.assets.length > 0);
  }, [status, focusedRow, derivedRegion, derivedPlantation, options, contextYear]);

  const mapItems = useMemo(() => {
    let source = [...(options?.divisions || [])];

    const targetPlantation = focusedRow?.plantation || filters.plantation;
    const targetRegion = focusedRow?.region || derivedRegion;
    const targetEstate = focusedRow?.estate || filters.estate;

    if (targetPlantation) {
      source = source.filter((item) => item.plantation === targetPlantation);
    }
    if (targetRegion) {
      source = source.filter((item) => item.region === targetRegion);
    }
    if (targetEstate) {
      source = source.filter((item) => item.estate === targetEstate);
    }

    const seen = new Set<string>();
    return source
      .filter((item) => {
        const key = `${item.plantation}|${item.region}|${item.estate}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .map((item) => {
        const query = [item.estate, displayRegion(item.region), displayPlantation(item.plantation), "Sri Lanka"]
          .filter(Boolean)
          .join(" ");
        return {
          ...item,
          mapQuery: query,
          mapUrl: buildMapLink(query),
        };
      });
  }, [options, filters.plantation, filters.estate, focusedRow, derivedRegion]);

  const mapFocusQuery = useMemo(() => {
    if (focusedRow?.estate) {
      return [focusedRow.estate, displayRegion(focusedRow.region), displayPlantation(focusedRow.plantation), "Sri Lanka"]
        .filter(Boolean)
        .join(" ");
    }
    if (filters.estate) {
      return [filters.estate, displayRegion(derivedRegion), displayPlantation(derivedPlantation), "Sri Lanka"]
        .filter(Boolean)
        .join(" ");
    }
    if (derivedRegion) {
      return [displayRegion(derivedRegion), "tea estates", "Sri Lanka"].join(" ");
    }
    if (derivedPlantation) {
      return [displayPlantation(derivedPlantation), "tea estates", "Sri Lanka"].join(" ");
    }
    return "Sri Lanka tea estates";
  }, [focusedRow, filters.estate, derivedRegion, derivedPlantation]);

  function updateFilter<K extends keyof QueryFilters>(key: K, value: QueryFilters[K]) {
    setError("");
    setFocusedRow(null);
    setFilters((current) => {
      const next = { ...current, [key]: value };

      if (key === "plantation") {
        next.region = "";
        next.estate = "";
        next.division = "";
      }

      if (key === "region") {
        next.estate = "";
        next.division = "";
      }

      return next;
    });
  }

  function updatePlantationChoice(nextChoice: string) {
    const allowedChoices = allowedPlantationChoices(access);
    if (!allowedChoices.some((item) => item.value === nextChoice)) return;
    setPlantationChoice(nextChoice);
    const plantationValue = nextChoice === "HAYLEYS" ? "" : nextChoice;
    updateFilter("plantation", plantationValue);
  }

  function updateMode(nextMode: ModeKey) {
    setError("");
    setFocusedRow(null);
    setFilters((current) => {
      const next = { ...current };

      if (
        nextMode === current.rankDir ||
        (nextMode === "above" && current.operator === ">") ||
        (nextMode === "below" && current.operator === "<")
      ) {
        next.rankDir = "";
        next.operator = "";
        next.value = "";
        next.count = "10";
        return next;
      }

      next.rankDir = "";
      next.operator = "";

      if (nextMode === "top" || nextMode === "bottom") {
        next.rankDir = nextMode;
        next.count = current.count || "10";
        next.value = "";
      }

      if (nextMode === "above") {
        next.operator = ">";
        next.value = current.value || "";
      }

      if (nextMode === "below") {
        next.operator = "<";
        next.value = current.value || "";
      }

      return next;
    });
  }

  function clearFilters() {
    const allowedChoices = allowedPlantationChoices(access);
    const defaultPlantation =
      access?.resolved_estate
        ? access.accessible_plantations[0] || ""
        : allowedChoices.some((item) => item.value === "HAYLEYS")
          ? ""
          : allowedChoices[0]?.value || "";

    const cleared: QueryFilters = {
      ...defaultFilters,
      plantation: defaultPlantation,
      estate: access?.resolved_estate || "",
      year: options?.years?.[0] || "",
      metric: options?.metrics?.[0]?.value || defaultFilters.metric,
    };

    setFilters(cleared);
    setPlantationChoice(defaultPlantation ? plantationChoiceFromValue(defaultPlantation) : "HAYLEYS");
    setRegionSummary(null);
    setEstateSummary(null);
    setViewerMode("");
    setFocusedRow(null);
    setError("");
  }

  function openViewer(nextMode: ViewerMode) {
    setViewerMode((current) => (current === nextMode ? "" : nextMode));
    requestAnimationFrame(() => {
      viewerSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function focusRow(row: QueryRow) {
    setFocusedRow((current) => {
      if (current && rowKey(current) === rowKey(row)) {
        return null;
      }
      return row;
    });
    setViewerMode("charts");
    requestAnimationFrame(() => {
      viewerSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  const visiblePlantationChoices = useMemo(() => allowedPlantationChoices(access), [access]);
  const exportUrl = buildExportCsvUrl(filters);

  return (
    <main className="pageShell">
      {loading ? (
        <section className="panelCard emptyPanel">Loading dashboard...</section>
      ) : !authUsername ? (
        <section className="panelCard emptyPanel">
          Open this page from the central login portal. Direct access is blocked.
        </section>
      ) : access?.access_mode === "restricted" ? (
        <section className="panelCard emptyPanel">
          {access.access_message || "This account does not have plantation dashboard access."}
        </section>
      ) : !status?.has_dataset ? (
        <section className="panelCard emptyPanel">
          No active dataset has been uploaded yet. The admin page will unlock this dashboard after
          monthly files are uploaded.
        </section>
      ) : (
        <>
          <section className="panelCard dashboardIntroCard">
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">Estate Performance</p>
                <h1 className="dashboardTitle">Yield Analysis Agent</h1>
                <p className="heroText" style={{ marginTop: 8 }}>
                  {access?.display_name || authUsername} · {access?.role?.toUpperCase() || "USER"}
                </p>
              </div>
              <div className="buttonRow wrap">
                <button
                  className={`btn ${viewerMode === "charts" ? "btnPrimary" : "btnGhost"}`}
                  onClick={() => openViewer("charts")}
                  type="button"
                >
                  Chart
                </button>
                <button
                  className={`btn ${viewerMode === "maps" ? "btnPrimary" : "btnGhost"}`}
                  onClick={() => openViewer("maps")}
                  type="button"
                >
                  Map
                </button>
                <a className="btn btnGhost" href={exportUrl} target="_blank" rel="noreferrer">
                  Export
                </a>
                <button className="btn btnSecondary" onClick={clearFilters} type="button">
                  Clear
                </button>
              </div>
            </div>

            <div className="filterRowCompact">
              <label className="field plantationField">
                <span>Plantation</span>
                <div className="plantationInlineGrid">
                  {visiblePlantationChoices.map((choice) => {
                    const checked = plantationChoice === choice.value;
                    return (
                      <label
                        className={`plantationInlineCard${checked ? " isActive" : ""}`}
                        key={choice.value}
                        title={choice.label}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => updatePlantationChoice(choice.value)}
                        />
                        <img className="plantationInlineLogo" src={choice.image} alt={choice.label} />
                      </label>
                    );
                  })}
                </div>
              </label>

              <label className="field">
                <span>Region</span>
                <select value={filters.region} onChange={(event) => updateFilter("region", event.target.value)}>
                  <option value="">All Regions</option>
                  {filteredRegions.map((item) => (
                    <option key={item} value={item}>
                      {displayRegion(item)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Estate</span>
                <select value={filters.estate} onChange={(event) => updateFilter("estate", event.target.value)}>
                  <option value="">All Estates</option>
                  {filteredEstates.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="filterRowCompact">
              <label className="field">
                <span>Year</span>
                <select value={filters.year} onChange={(event) => updateFilter("year", event.target.value)}>
                  {options?.years.map((item) => (
                    <option key={item} value={item}>
                      {prettyYearLabel(item)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Metric</span>
                <select value={filters.metric} onChange={(event) => updateFilter("metric", event.target.value)}>
                  {options?.metrics.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Benchmark</span>
                <select
                  value={filters.benchmarkMetric}
                  onChange={(event) => updateFilter("benchmarkMetric", event.target.value)}
                >
                  <option value="">No Benchmark</option>
                  {options?.benchmarks.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="filterRowCompact thirdRow">
              <div className="field directionField">
                <span>Direction</span>
                <div className="checkboxGrid">
                  {[
                    { value: "top", label: "Top" },
                    { value: "bottom", label: "Bottom" },
                    { value: "above", label: "Above" },
                    { value: "below", label: "Below" },
                  ].map((item) => {
                    const checked = activeMode === item.value;
                    return (
                      <label className={`choiceChip smallChoice${checked ? " isActive" : ""}`} key={item.value}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => updateMode(item.value as ModeKey)}
                        />
                        <span>{item.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {activeMode === "top" || activeMode === "bottom" ? (
                <label className="field compactActionField">
                  <span>Count</span>
                  <input
                    type="number"
                    min="1"
                    value={filters.count}
                    onChange={(event) => updateFilter("count", event.target.value)}
                    placeholder="10"
                  />
                </label>
              ) : activeMode === "above" || activeMode === "below" ? (
                <label className="field compactActionField">
                  <span>Threshold Value</span>
                  <input
                    type="number"
                    value={filters.value}
                    onChange={(event) => updateFilter("value", event.target.value)}
                    placeholder="500"
                  />
                </label>
              ) : (
                <div className="compactActionSpacer" />
              )}
            </div>

            {error ? <pre className="errorText">{error}</pre> : null}
          </section>

          {showSummaries ? (
            <section className="summaryGrid">
              {(filters.region || filters.estate) && regionSummary ? (
                <article className="panelCard">
                  <div className="summaryCardHeader">
                    <h2>Region Summary</h2>
                    <p>{regionSummary.region_label || displayRegion(regionSummary.region)}</p>
                    <span>{prettyYearLabel(regionSummary.year)}</span>
                  </div>
                  <div className="statGrid">
                    <div className="statTile">
                      <span>Regional Average</span>
                      <strong>{formatNumber(regionSummary.regional_average)}</strong>
                    </div>
                    <div className="statTile">
                      <span>Benchmark</span>
                      <strong>{formatNumber(regionSummary.benchmark)}</strong>
                    </div>
                  </div>
                </article>
              ) : null}

              {filters.estate && estateSummary ? (
                <article className="panelCard">
                  <div className="summaryCardHeader">
                    <h2>Estate Summary</h2>
                    <p>{estateSummary.estate}</p>
                    <span>{prettyYearLabel(estateSummary.year)}</span>
                  </div>
                  <div className="statGrid">
                    <div className="statTile">
                      <span>Estate Yield</span>
                      <strong>{formatNumber(estateSummary.estate_yield)}</strong>
                    </div>
                    <div className="statTile">
                      <span>Estate Extent</span>
                      <strong>{formatNumber(estateSummary.estate_extent, 2)} ha</strong>
                    </div>
                    <div className="statTile">
                      <span>Regional Average</span>
                      <strong>{formatNumber(estateSummary.regional_average)}</strong>
                    </div>
                    <div className="statTile">
                      <span>Benchmark</span>
                      <strong>{formatNumber(estateSummary.benchmark)}</strong>
                    </div>
                  </div>
                </article>
              ) : null}
            </section>
          ) : null}

          {viewerMode ? (
            <section className="panelCard viewerPanel" ref={viewerSectionRef}>
              <div className="viewerToolbar">
                {focusedRow ? (
                  <div className="softBadge">
                    {focusedRow.estate || focusedRow.division || displayRegion(focusedRow.region)} ·{" "}
                    {prettyYearLabel(focusedRow.year || "")}
                  </div>
                ) : null}
                <button className="btn btnSecondary" onClick={() => setViewerMode("")} type="button">
                  Hide
                </button>
              </div>

              {viewerMode === "charts" ? (
                !status?.active_report ? (
                  <div className="emptyPanel">
                    Generate reports from the admin page first. Then the public dashboard will show
                    the real project chart images here.
                  </div>
                ) : !reportChartGroups.length ? (
                  <div className="emptyPanel">No generated chart images match the current selection.</div>
                ) : (
                  <div className="chartGalleryGrid simpleChartGallery">
                    {reportChartGroups.map((group) => (
                      <article className="reportRegionCard compactRegionCard" key={group.region}>
                        <div className="reportAssetGrid">
                          {group.assets.map((asset) => (
                            <a
                              className="reportAssetCard"
                              key={`${group.region}-${asset.title}-${asset.page_png}`}
                              href={mediaUrl(asset.page_png || asset.png || asset.jpg)}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <img
                                src={mediaUrl(asset.page_png || asset.png || asset.jpg)}
                                alt={`${group.regionLabel} ${asset.cleanTitle}`}
                              />
                              <div className="reportAssetMeta compactAssetMeta">
                                <strong>{asset.cleanTitle}</strong>
                                {!focusedRow && !derivedRegion && reportChartGroups.length > 1 ? (
                                  <span>{group.regionLabel}</span>
                                ) : null}
                              </div>
                            </a>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                )
              ) : !mapItems.length ? (
                <div className="emptyPanel">No estate map links match the current selection.</div>
              ) : (
                <div className="mapViewerStack">
                  <div className="mapEmbedShell">
                    <iframe
                      className="mapEmbed"
                      src={buildMapEmbedUrl(mapFocusQuery)}
                      title="Estate map"
                      loading="lazy"
                      referrerPolicy="no-referrer-when-downgrade"
                    />
                  </div>
                  <div className="mapGrid compactMapGrid">
                    {mapItems.map((item) => (
                      <article className="mapCard" key={`${item.plantation}-${item.region}-${item.estate}`}>
                        <h3>{item.estate}</h3>
                        <p className="softNote compactNote">{displayRegion(item.region)}</p>
                        <a className="btn btnGhost" href={item.mapUrl} target="_blank" rel="noreferrer">
                          Open Map
                        </a>
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </section>
          ) : null}

          <section className="panelCard">
            <div className="sectionHeader compact">
              <div>
                <h2>Results</h2>
              </div>
            </div>

            <div className="tableWrap">
              <table className="resultTable">
                <thead>
                  <tr>
                    <th>Plantation</th>
                    <th>Region</th>
                    <th>Estate</th>
                    <th>Division</th>
                    <th>Year</th>
                    <th className="textRight">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {!displayRows.length ? (
                    <tr>
                      <td colSpan={6} className="tableEmpty">
                        {running ? "Updating results..." : "No rows match the current filters."}
                      </td>
                    </tr>
                  ) : (
                    displayRows.map((row) => {
                      const selected = focusedRow && rowKey(row) === rowKey(focusedRow);
                      return (
                        <tr
                          key={rowKey(row)}
                          className={`clickableRow${selected ? " isSelected" : ""}`}
                          onClick={() => focusRow(row)}
                        >
                          <td>{row.plantation_label || displayPlantation(row.plantation)}</td>
                          <td>{row.region_label || displayRegion(row.region)}</td>
                          <td>{row.estate || "—"}</td>
                          <td>{row.division || "—"}</td>
                          <td>{row.year ? prettyYearLabel(row.year) : "—"}</td>
                          <td className="textRight">{formatNumber(row.value)}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {status.active_report?.downloads ? (
            <section className="panelCard">
              <div className="sectionHeader compact">
                <div>
                  <h2>Downloads</h2>
                </div>
                <div className="buttonRow">
                  <a
                    className="btn btnGhost"
                    href={mediaUrl(status.active_report.downloads.excel)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Excel
                  </a>
                  <a
                    className="btn btnGhost"
                    href={mediaUrl(status.active_report.downloads.pdf)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    PDF
                  </a>
                  <a
                    className="btn btnGhost"
                    href={mediaUrl(status.active_report.downloads.zip)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    ZIP
                  </a>
                </div>
              </div>
            </section>
          ) : null}

          <section className="pageFooterBar">
            <a className="btn btnGhost" href="/admin">
              Admin Page
            </a>
          </section>
        </>
      )}
    </main>
  );
}
