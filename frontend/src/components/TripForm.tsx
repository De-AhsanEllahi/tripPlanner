import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Box,
  Button,
  CircularProgress,
  Slider,
  Stack,
  TextField,
  Typography,
  Paper,
  Alert,
} from "@mui/material";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import type { TripFormValues } from "../types";

const schema = z.object({
  current_location: z.string().min(3, "Enter your current location"),
  pickup_location: z.string().min(3, "Enter the pickup location"),
  dropoff_location: z.string().min(3, "Enter the dropoff location"),
  current_cycle_used: z.number().min(0).max(70),
});

interface Props {
  onSubmit: (values: TripFormValues) => void;
  loading: boolean;
  error?: string;
}

export default function TripForm({ onSubmit, loading, error }: Props) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<TripFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      current_location: "",
      pickup_location: "",
      dropoff_location: "",
      current_cycle_used: 0,
    },
  });

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, mx: "auto", mt: 4 }}>
      <Stack direction="row" spacing={1} alignItems="center" mb={3}>
        <DirectionsCarIcon color="primary" fontSize="large" />
        <Typography variant="h5" fontWeight={700}>
          ELD Trip Planner
        </Typography>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Stack spacing={3}>
          <Controller
            name="current_location"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Current Location"
                placeholder="e.g. Dallas, TX"
                error={!!errors.current_location}
                helperText={errors.current_location?.message}
                fullWidth
                inputProps={{ "aria-label": "Current location" }}
              />
            )}
          />

          <Controller
            name="pickup_location"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Pickup Location"
                placeholder="e.g. Houston, TX"
                error={!!errors.pickup_location}
                helperText={errors.pickup_location?.message}
                fullWidth
                inputProps={{ "aria-label": "Pickup location" }}
              />
            )}
          />

          <Controller
            name="dropoff_location"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Dropoff Location"
                placeholder="e.g. Chicago, IL"
                error={!!errors.dropoff_location}
                helperText={errors.dropoff_location?.message}
                fullWidth
                inputProps={{ "aria-label": "Dropoff location" }}
              />
            )}
          />

          <Box>
            <Typography gutterBottom>
              Current Cycle Used (hours):{" "}
              <Controller
                name="current_cycle_used"
                control={control}
                render={({ field }) => (
                  <Typography
                    component="span"
                    fontWeight={700}
                    color={field.value >= 60 ? "error" : "text.primary"}
                  >
                    {field.value} / 70
                  </Typography>
                )}
              />
            </Typography>
            <Controller
              name="current_cycle_used"
              control={control}
              render={({ field }) => (
                <Slider
                  {...field}
                  min={0}
                  max={70}
                  step={0.5}
                  marks={[
                    { value: 0, label: "0" },
                    { value: 35, label: "35" },
                    { value: 70, label: "70" },
                  ]}
                  valueLabelDisplay="auto"
                  aria-label="Current cycle used hours"
                  onChange={(_, val) => field.onChange(val)}
                  sx={{
                    "& .MuiSlider-track": {
                      bgcolor: field.value >= 60 ? "error.main" : "primary.main",
                    },
                  }}
                />
              )}
            />
            {errors.current_cycle_used && (
              <Typography color="error" variant="caption">
                {errors.current_cycle_used.message}
              </Typography>
            )}
          </Box>

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : null}
            aria-label="Generate trip plan"
          >
            {loading ? "Calculating Route..." : "Generate Trip Plan"}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}
