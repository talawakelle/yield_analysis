'use client';

import type { ChartResponse } from "../lib/api";

type ChartModalProps = {
  open: boolean;
  loading: boolean;
  data: ChartResponse | null;
  onClose: () => void;
};

function formatNumber(value: number | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

export default function ChartModal({ open, loading, data, onClose }: ChartModalProps) {
  if (!open) return null;

  const maxValue =
    data?.bars?.reduce((max, item) => Math.max(max, item.value || 0), 0) || 1;

  return (
    <div className="modalShell" onClick={onClose}>
      <div className="modalCard" onClick={(event) => event.stopPropagation()}>
        <div className="modalHeader">
          <div>
            <p className="eyebrow">Region chart</p>
            <h3>{data?.title || "Loading chart"}</h3>
          </div>
          <button className="iconCircle" onClick={onClose} type="button">
            ✕
          </button>
        </div>

        {loading ? (
          <div className="emptyPanel">Building chart...</div>
        ) : !data || data.bars.length === 0 ? (
          <div className="emptyPanel">No chart data available for this selection.</div>
        ) : (
          <div className="chartModalBody">
            <div className="referenceGrid">
              <div className="miniStat">
                <span>Metric</span>
                <strong>{data.metric_label}</strong>
              </div>
              <div className="miniStat">
                <span>Benchmark</span>
                <strong>{formatNumber(data.reference?.benchmark)}</strong>
              </div>
              <div className="miniStat">
                <span>Regional average</span>
                <strong>{formatNumber(data.reference?.regional_average)}</strong>
              </div>
            </div>

            <div className="barList">
              {data.bars.map((item) => {
                const width = Math.max((item.value / maxValue) * 100, 4);
                return (
                  <div
                    className={`barRow ${item.highlight ? "isHighlighted" : ""}`}
                    key={`${item.label}-${item.value}`}
                  >
                    <div className="barMeta">
                      <strong>{item.label}</strong>
                      <span>{formatNumber(item.value)}</span>
                    </div>
                    <div className="barTrack">
                      <div className="barFill" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {data.focus_label ? (
              <p className="chartNote">
                Highlighted selection: <strong>{data.focus_label}</strong>
              </p>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
