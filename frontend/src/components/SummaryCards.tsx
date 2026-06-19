import { Box, Grid, Paper, Typography, Stack, Divider } from "@mui/material";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import LocalGasStationIcon from "@mui/icons-material/LocalGasStation";
import HotelIcon from "@mui/icons-material/Hotel";
import ScheduleIcon from "@mui/icons-material/Schedule";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import TimerIcon from "@mui/icons-material/Timer";
import CoffeeIcon from "@mui/icons-material/Coffee";
import LoopIcon from "@mui/icons-material/Loop";
import type { Trip } from "../types";

function fmt(h: number): string {
  const days = Math.floor(h / 24);
  const hrs = Math.floor(h % 24);
  const mins = Math.round((h % 1) * 60);
  if (days > 0) return `${days}d ${hrs}h ${mins}m`;
  return `${hrs}h ${mins}m`;
}

interface CardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color?: string;
}

function StatCard({ icon, label, value, color = "primary.main" }: CardProps) {
  return (
    <Paper elevation={2} sx={{ p: 2, height: "100%", borderTop: 3, borderColor: color }}>
      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
        <Box sx={{ bgcolor: `${color}20`, borderRadius: 1, p: 1, color }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
            {label}
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {value}
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
}

interface Props {
  trip: Trip;
}

export default function SummaryCards({ trip }: Props) {
  const fuelStops = trip.stops.filter((s) => s.stop_type === "fuel").length;
  const breakStops = trip.stops.filter((s) => s.stop_type === "break").length;
  const restartStops = trip.stops.filter((s) => s.stop_type === "restart").length;
  const cycleRemaining = Math.max(0, 70 - trip.current_cycle_used).toFixed(1);

  const cards: CardProps[] = [
    { icon: <DirectionsCarIcon />, label: "Total Distance", value: `${trip.distance_miles?.toFixed(0) ?? "—"} miles`, color: "primary.main" },
    { icon: <TimerIcon />, label: "Drive Time", value: fmt(trip.duration_hours ?? 0), color: "info.main" },
    { icon: <ScheduleIcon />, label: "Trip Duration (ETA)", value: fmt(trip.eta_hours ?? 0), color: "warning.main" },
    { icon: <CalendarTodayIcon />, label: "Days Required", value: `${trip.days_required ?? "—"} days`, color: "secondary.main" },
    { icon: <LocalGasStationIcon />, label: "Fuel Stops", value: `${fuelStops}`, color: "error.main" },
    { icon: <CoffeeIcon />, label: "Break Stops", value: `${breakStops}`, color: "success.main" },
    { icon: <HotelIcon />, label: "Overnight Rests", value: `${trip.stops.filter((s) => s.stop_type === "rest").length}`, color: "info.dark" },
    { icon: <LoopIcon />, label: "34-hr Restarts", value: restartStops > 0 ? `${restartStops}` : "None", color: restartStops > 0 ? "error.main" : "success.main" },
    { icon: <LoopIcon />, label: "Cycle Remaining", value: `${cycleRemaining} / 70 hrs`, color: Number(cycleRemaining) < 11 ? "error.main" : "success.main" },
  ];

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Trip Summary</Typography>
      <Divider sx={{ mb: 2 }} />
      <Grid container spacing={2}>
        {cards.map((card) => (
          <Grid key={card.label} size={{ xs: 6, sm: 4, md: 3 }}>
            <StatCard {...card} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
