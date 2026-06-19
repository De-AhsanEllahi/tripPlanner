import { useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  Divider,
  Stack,
  Tab,
  Tabs,
  Typography,
  Alert,
  Paper,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import { getTripPdfUrl } from "../api/trips";
import type { DailyLog } from "../types";

const DAY_START = 6;
const STATUS_COLOR: Record<string, string> = {
  OFF_DUTY: "#94a3b8",
  SLEEPER_BERTH: "#818cf8",
  DRIVING: "#3b82f6",
  ON_DUTY_NOT_DRIVING: "#f59e0b",
};
const STATUS_LABEL: Record<string, string> = {
  OFF_DUTY: "Off Duty",
  SLEEPER_BERTH: "Sleeper",
  DRIVING: "Driving",
  ON_DUTY_NOT_DRIVING: "On Duty",
};
const STATUS_ORDER = ["OFF_DUTY", "SLEEPER_BERTH", "DRIVING", "ON_DUTY_NOT_DRIVING"];

function absHourToDay(abs: number) {
  return (DAY_START + abs) % 24;
}

interface EldGridProps {
  log: DailyLog;
}

function EldGrid({ log }: EldGridProps) {
  const GRID_H = 140;
  const ROW_H = GRID_H / 4;
  const W = 700;
  const LEFT = 90;
  const GRID_W = W - LEFT - 16;

  function timeToX(absHour: number): number {
    const dayHour = absHourToDay(absHour);
    return LEFT + (dayHour / 24) * GRID_W;
  }

  function rowY(rowIdx: number): number {
    return rowIdx * ROW_H + ROW_H / 2;
  }

  const segs = [...(log.log_data ?? [])].sort((a, b) => a.start - b.start);

  // Build path of horizontal + vertical lines
  const lines: React.ReactNode[] = [];
  let prevRow: number | null = null;
  let prevX: number | null = null;

  segs.forEach((seg, i) => {
    const row = STATUS_ORDER.indexOf(seg.status);
    if (row < 0) return;
    const x1 = timeToX(seg.start);
    const x2 = timeToX(seg.end);
    if (x2 <= x1) return;
    const cy = rowY(row);
    const color = STATUS_COLOR[seg.status] ?? "#888";

    if (prevRow !== null && prevRow !== row && prevX !== null) {
      lines.push(
        <line key={`v-${i}`} x1={prevX} y1={rowY(prevRow)} x2={prevX} y2={cy} stroke="#334155" strokeWidth={1.5} />
      );
    }
    lines.push(
      <line key={`h-${i}`} x1={x1} y1={cy} x2={x2} y2={cy} stroke={color} strokeWidth={2.5} />
    );
    prevRow = row;
    prevX = x2;
  });

  return (
    <Box overflow="auto">
      <svg width={W} height={GRID_H + 28} style={{ display: "block", fontFamily: "monospace" }}>
        {/* Row labels */}
        {STATUS_ORDER.map((status, i) => (
          <text key={status} x={4} y={rowY(i) + 4} fontSize={9} fill="#475569">
            {STATUS_LABEL[status]}
          </text>
        ))}

        {/* Hour lines */}
        {Array.from({ length: 25 }, (_, h) => {
          const x = LEFT + (h / 24) * GRID_W;
          return (
            <g key={h}>
              <line x1={x} y1={0} x2={x} y2={GRID_H} stroke="#e2e8f0" strokeWidth={h % 6 === 0 ? 1 : 0.5} />
              {h % 2 === 0 && (
                <text x={x} y={GRID_H + 12} fontSize={8} textAnchor="middle" fill="#94a3b8">
                  {String(h).padStart(2, "0")}
                </text>
              )}
            </g>
          );
        })}

        {/* Row dividers */}
        {[0, 1, 2, 3, 4].map((i) => (
          <line key={i} x1={LEFT} y1={i * ROW_H} x2={W - 16} y2={i * ROW_H} stroke="#cbd5e1" strokeWidth={0.8} />
        ))}

        {/* Status lines */}
        {lines}
      </svg>
    </Box>
  );
}

interface Props {
  logs: DailyLog[];
  tripId: number;
}

export default function LogViewer({ logs, tripId }: Props) {
  const [tab, setTab] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [dlError, setDlError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloading(true);
    setDlError(null);
    try {
      const url = getTripPdfUrl(tripId);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trip_${tripId}_eld_logs.pdf`;
      a.click();
    } catch {
      setDlError("PDF download failed. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Box mt={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="h6" fontWeight={700}>
          ELD Daily Logs
        </Typography>
        <Button
          variant="contained"
          color="error"
          startIcon={downloading ? <CircularProgress size={16} color="inherit" /> : <PictureAsPdfIcon />}
          endIcon={<DownloadIcon />}
          onClick={handleDownload}
          disabled={downloading}
          aria-label="Download PDF logs"
        >
          {downloading ? "Generating..." : "Download PDF"}
        </Button>
      </Stack>
      <Divider sx={{ mb: 2 }} />

      {dlError && <Alert severity="error" sx={{ mb: 2 }}>{dlError}</Alert>}

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        aria-label="Daily log tabs"
      >
        {logs.map((log) => (
          <Tab key={log.day_number} label={`Day ${log.day_number}`} id={`log-tab-${log.day_number}`} />
        ))}
      </Tabs>

      {logs.map((log, i) => (
        <Box
          key={log.day_number}
          role="tabpanel"
          hidden={tab !== i}
          id={`log-tabpanel-${log.day_number}`}
          aria-labelledby={`log-tab-${log.day_number}`}
          mt={2}
        >
          {tab === i && (
            <Paper elevation={1} sx={{ p: 2 }}>
              <Stack direction="row" spacing={2} mb={1} flexWrap="wrap">
                <Typography variant="body2" fontWeight={600}>
                  Day {log.day_number}
                </Typography>
                {Object.entries(log.totals ?? {}).map(([status, hours]) =>
                  (hours as number) > 0 ? (
                    <Typography key={status} variant="caption" sx={{ color: STATUS_COLOR[status] ?? "#333" }}>
                      {STATUS_LABEL[status] ?? status}: {(hours as number).toFixed(2)}h
                    </Typography>
                  ) : null
                )}
              </Stack>

              <EldGrid log={log} />

              {log.remarks && log.remarks.length > 0 && (
                <Box mt={1.5}>
                  <Typography variant="caption" fontWeight={600}>Remarks: </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {log.remarks.join(" → ")}
                  </Typography>
                </Box>
              )}
            </Paper>
          )}
        </Box>
      ))}
    </Box>
  );
}
