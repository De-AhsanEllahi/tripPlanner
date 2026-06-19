import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography, Box } from "@mui/material";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import HomePage from "./pages/HomePage";
import ResultsPage from "./pages/ResultsPage";
import type { Trip } from "./types";

const queryClient = new QueryClient();

const theme = createTheme({
  palette: {
    primary: { main: "#1d4ed8" },
    secondary: { main: "#7c3aed" },
    background: { default: "#f8fafc" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 8 },
});

export default function App() {
  const [trip, setTrip] = useState<Trip | null>(null);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppBar position="static" elevation={0} sx={{ bgcolor: "primary.main" }}>
          <Toolbar>
            <DirectionsCarIcon sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={700} sx={{ flexGrow: 1 }}>
              ELD Trip Planner
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              FMCSA Compliant · 70-Hour/8-Day Rule
            </Typography>
          </Toolbar>
        </AppBar>

        <Box component="main" minHeight="calc(100vh - 64px)" bgcolor="background.default">
          {trip ? (
            <ResultsPage trip={trip} onBack={() => setTrip(null)} />
          ) : (
            <HomePage onTripCreated={setTrip} />
          )}
        </Box>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
