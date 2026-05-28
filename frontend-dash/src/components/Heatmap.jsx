import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "leaflet.heat";
import { useState, useEffect } from "react";

function HeatLayer({ heatData }) {
  const map = useMap();

  useEffect(() => {
    if (!map || !heatData.length) return;

    // The backend sends [lat, lon, cases]
    // We divide cases by a rough max factor (e.g. 120) to normalize intensity between 0 and 1
    const formattedData = heatData.map(point => [
      point[0],
      point[1],
      point[2] / 120
    ]);

    const heatLayer = L.heatLayer(formattedData, {
      radius: 80,
      blur: 60,
      minOpacity: 0.5,
      maxZoom: 10,
      gradient: {
        0.2: "blue",
        0.4: "lime",
        0.6: "yellow",
        0.8: "orange",
        1.0: "red"
      }
    });

    heatLayer.addTo(map);

    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, heatData]);

  return null;
}

function Heatmap() {
  const [heatData, setHeatData] = useState([]);

  useEffect(() => {
    // 🔌 WIRED TO LIVE BACKEND
    fetch("http://localhost:5000/api/heatmap-data")
      .then(res => res.json())
      .then(data => {
        setHeatData(data);
      })
      .catch(error => console.error("Map Data Error:", error));
  }, []);

  return (
    <div style={{ height: "100vh", width: "100%" }}>
      <MapContainer
        center={[20.5937, 78.9629]}
        zoom={5}
        style={{ height: "100vh", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
        />
        <HeatLayer heatData={heatData} />
      </MapContainer>
    </div>
  );
}

export default Heatmap;