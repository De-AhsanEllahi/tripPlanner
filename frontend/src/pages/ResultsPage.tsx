import { useState } from "react";
import {
  Box,
  Button,
  Container,
  Divider,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
  Chip,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import MapIcon from "@mui/icons-material/Map";
import TimelineIcon from "@mui/icons-material/Timeline";
import ListAltIcon from "@mui/icons-material/ListAlt";
import TableChartIcon from "@mui/icons-material/TableChart";

import TripMap from "../components/TripMap";
import SummaryCards from "../components/SummaryCards";
import TimelineView from "../components/TimelineView";
import LogViewer from "../components/LogViewer";
import StopsTable from "../components/StopsTable";
import type { Trip } from "../types";

interface Props {
  trip: Trip;
  onBack: () => void;
}

const TABS = [
  { label: "Map", icon: <MapIcon /> },
  { label: "Timeline", icon: <TimelineIcon /> },
  { label: "Stops", icon: <TableChartIcon /> },
  { label: "ELD Logs", icon: <ListAltIcon /> },
];

export default function ResultsPage({ trip, onBack }: Props) {
  const [tab, setTab] = useState(0);

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" alignItems={{ sm: "center" }} mb={3} spacing={2}>
        <Box>
          <Button startIcon={<ArrowBackIcon />} onClick={onBack} sx={{ mb: 1 }}>
            New Trip
          </Button>
          <Typography variant="h5" fontWeight={700}>
            {trip.current_location} → {trip.dropoff_location}
          </Typography>
          <Stack direction="row" spacing={1} mt={0.5} flexWrap="wrap">
            <Chip label={`Via ${trip.pickup_location}`} size="small" variant="outlined" />
            <Chip label={`${trip.distance_miles?.toFixed(0)} miles`} size="small" color="primary" />
            <Chip label={`${trip.days_required} days`} size="small" color="secondary" />
          </Stack>
        </Box>
      </Stack>

      {/* Summary cards */}
      <SummaryCards trip={trip} />

      <Divider sx={{ my: 3 }} />

      {/* Tab nav */}
      <Paper elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          aria-label="Trip results tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          {TABS.map((t, i) => (
            <Tab key={t.label} label={t.label} icon={t.icon} iconPosition="start" id={`result-tab-${i}`} />
          ))}
        </Tabs>
      </Paper>

      {/* Map */}
      <Box role="tabpanel" hidden={tab !== 0} id="result-tab-panel-0" mt={2}>
        {tab === 0 && <TripMap trip={trip} />}
      </Box>

      {/* Timeline */}
      <Box role="tabpanel" hidden={tab !== 1} id="result-tab-panel-1">
        {tab === 1 && <TimelineView logs={trip.daily_logs} />}
      </Box>

      {/* Stops */}
      <Box role="tabpanel" hidden={tab !== 2} id="result-tab-panel-2">
        {tab === 2 && <StopsTable stops={trip.stops} />}
      </Box>

      {/* Logs */}
      <Box role="tabpanel" hidden={tab !== 3} id="result-tab-panel-3">
        {tab === 3 && <LogViewer logs={trip.daily_logs} tripId={trip.id} />}
      </Box>
    </Container>
  );
}
