import {
  Box,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
} from "@mui/material";
import LocalGasStationIcon from "@mui/icons-material/LocalGasStation";
import CoffeeIcon from "@mui/icons-material/Coffee";
import HotelIcon from "@mui/icons-material/Hotel";
import LoopIcon from "@mui/icons-material/Loop";
import PlaceIcon from "@mui/icons-material/Place";
import InventoryIcon from "@mui/icons-material/Inventory";
import type { Stop } from "../types";

const STOP_META: Record<string, { label: string; icon: React.ReactNode; color: "default" | "error" | "warning" | "success" | "secondary" | "primary" | "info" }> = {
  fuel: { label: "Fuel Stop", icon: <LocalGasStationIcon fontSize="small" />, color: "error" },
  break: { label: "Break", icon: <CoffeeIcon fontSize="small" />, color: "warning" },
  rest: { label: "Overnight Rest", icon: <HotelIcon fontSize="small" />, color: "secondary" },
  restart: { label: "34-Hr Restart", icon: <LoopIcon fontSize="small" />, color: "error" },
  pickup: { label: "Pickup", icon: <InventoryIcon fontSize="small" />, color: "success" },
  dropoff: { label: "Dropoff", icon: <PlaceIcon fontSize="small" />, color: "primary" },
};

function fmtDuration(h: number): string {
  if (h >= 1) {
    const hrs = Math.floor(h);
    const mins = Math.round((h - hrs) * 60);
    return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h`;
  }
  return `${Math.round(h * 60)}m`;
}

interface Props {
  stops: Stop[];
}

export default function StopsTable({ stops }: Props) {
  return (
    <Box mt={3}>
      <Typography variant="h6" fontWeight={700} mb={2}>
        Planned Stops
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <TableContainer component={Paper} elevation={1}>
        <Table size="small" aria-label="Planned stops table">
          <TableHead>
            <TableRow sx={{ bgcolor: "grey.100" }}>
              <TableCell>#</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Day</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stops.map((stop, idx) => {
              const meta = STOP_META[stop.stop_type] ?? { label: stop.stop_type, icon: null, color: "default" as const };
              return (
                <TableRow key={stop.id} hover>
                  <TableCell>{idx + 1}</TableCell>
                  <TableCell>
                    <Chip
                      icon={meta.icon as React.ReactElement}
                      label={meta.label}
                      color={meta.color}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{stop.location}</TableCell>
                  <TableCell>Day {stop.day_number}</TableCell>
                  <TableCell>{fmtDuration(stop.duration_hours)}</TableCell>
                  <TableCell sx={{ maxWidth: 300, fontSize: 12 }}>
                    <Typography variant="caption" color="text.secondary">
                      {stop.reason}
                    </Typography>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
