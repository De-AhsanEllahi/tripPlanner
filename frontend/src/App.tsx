import { useEffect, useState } from "react";
import { getTrips } from "./api/trips";

function App() {
  const [trips, setTrips] = useState([]);

  useEffect(() => {
    getTrips().then(setTrips);
  }, []);

  return (
    <div>
      <h1>Trips</h1>
      <pre>{JSON.stringify(trips, null, 2)}</pre>
    </div>
  );
}

export default App;