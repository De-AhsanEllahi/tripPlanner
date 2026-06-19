import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Chip,
  Stack,
  Typography,
  Divider,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import type { DailyLog, Segment } from "../types";

const STATUS_COLOR: Record<string, "default" | "primary" | "secondary" | "error" | "warning" | "info" | "success"> = {
  OFF_DUTY: "default",
  SLEEPER_BERTH: "secondary",
  DRIVING: "primary",
  ON_DUTY_NOT_DRIVING: "warning",
};

const STATUS_LABEL: Record<string, string> = {
  OFF_DUTY: "Off Duty",
  SLEEPER_BERTH: "Sleeper",
  DRIVING: "Driving",
  ON_DUTY_NOT_DRIVING: "On Duty",
};

const DAY_START = 6; // 06:00

function absToTime(absHour: number): string {
  const totalHours = DAY_START + absHour;
  const h = Math.floor(totalHours % 24);
  const m = Math.round((totalHours % 1) * 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function fmtDuration(h: number): string {
  const hrs = Math.floor(h);
  const mins = Math.round((h - hrs) * 60);
  if (hrs === 0) return `${mins}m`;
  if (mins === 0) return `${hrs}h`;
  return `${hrs}h ${mins}m`;
}

interface SegmentRowProps {
  seg: Segment;
}

function SegmentRow({ seg }: SegmentRowProps) {
  return (
    <Stack
      direction="row"
      spacing={2}
      alignItems="flex-start"
      py={0.75}
      px={1}
      sx={{
        borderLeft: 3,
        borderColor: `${STATUS_COLOR[seg.status]}.main`,
        borderRadius: 0.5,
        "&:hover": { bgcolor: "action.hover" },
      }}
    >
      <Box sx={{ minWidth: 90 }}>
        <Typography variant="caption" fontWeight={600} display="block">
          {absToTime(seg.start)}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          → {absToTime(seg.end)}
        </Typography>
      </Box>

      <Box sx={{ flex: 1 }}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Chip
            label={STATUS_LABEL[seg.status] ?? seg.status}
            color={STATUS_COLOR[seg.status] ?? "default"}
            size="small"
          />
          <Typography variant="caption" color="text.secondary">
            {fmtDuration(seg.duration)}
          </Typography>
        </Stack>
        <Typography variant="caption" display="block" mt={0.25}>
          {seg.location}
        </Typography>
        {seg.note && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ fontStyle: "italic" }}>
            {seg.note}
          </Typography>
        )}
      </Box>
    </Stack>
  );
}

interface Props {
  logs: DailyLog[];
}

export default function TimelineView({ logs }: Props) {
  return (
    <Box mt={3}>
      <Typography variant="h6" fontWeight={700} mb={2}>
        Daily Timeline
      </Typography>
      <Divider sx={{ mb: 2 }} />
      {logs.map((log) => (
        <Accordion key={log.day_number} defaultExpanded={log.day_number === 1}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Stack direction="row" spacing={2} alignItems="center" width="100%">
              <Typography fontWeight={700}>
                {log.date_label} — Day {log.day_number}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {Object.entries(log.totals ?? {}).map(([status, hours]) =>
                  hours > 0 ? (
                    <Chip
                      key={status}
                      label={`${STATUS_LABEL[status] ?? status}: ${fmtDuration(hours as number)}`}
                      color={STATUS_COLOR[status] ?? "default"}
                      size="small"
                      variant="outlined"
                    />
                  ) : null
                )}
              </Stack>
            </Stack>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 1 }}>
            <Stack spacing={0.5}>
              {(log.log_data ?? []).map((seg, i) => (
                <SegmentRow key={i} seg={seg} />
              ))}
            </Stack>
            {log.remarks && log.remarks.length > 0 && (
              <Box mt={1.5} p={1} bgcolor="grey.50" borderRadius={1}>
                <Typography variant="caption" fontWeight={600}>
                  Locations: {" "}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {log.remarks.join(" → ")}
                </Typography>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
