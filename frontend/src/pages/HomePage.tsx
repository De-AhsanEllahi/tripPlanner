import { useState } from "react";
import { Container, Box, Typography, LinearProgress, Alert, Stepper, Step, StepLabel } from "@mui/material";
import TripForm from "../components/TripForm";
import { createTrip } from "../api/trips";
import type { Trip, TripFormValues } from "../types";

interface Props {
  onTripCreated: (trip: Trip) => void;
}

const STEPS = ["Geocoding locations", "Calculating route", "Applying HOS rules", "Generating logs"];

export default function HomePage({ onTripCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(-1);
  const [error, setError] = useState<string | undefined>();

  const handleSubmit = async (values: TripFormValues) => {
    setLoading(true);
    setError(undefined);
    setStep(0);

    try {
      // Simulate step progression for UX (actual work is one API call)
      const stepTimer = setInterval(() => {
        setStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
      }, 1800);

      const trip = await createTrip(values);
      clearInterval(stepTimer);
      onTripCreated(trip);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
        "Something went wrong. Check your locations and try again.";
      setError(msg);
      setStep(-1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box py={6} textAlign="center">
        <Typography variant="h3" fontWeight={800} gutterBottom>
          ELD Trip Planner
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" mb={4}>
          FMCSA-compliant route planning with HOS enforcement and daily log generation
        </Typography>
      </Box>

      <TripForm onSubmit={handleSubmit} loading={loading} error={error} />

      {loading && (
        <Box mt={4} maxWidth={600} mx="auto">
          <Stepper activeStep={step} alternativeLabel>
            {STEPS.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          <LinearProgress sx={{ mt: 3, borderRadius: 1 }} />
          <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
            {STEPS[step] ?? "Starting..."}
          </Typography>
        </Box>
      )}
    </Container>
  );
}
