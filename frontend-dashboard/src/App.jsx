import "./App.css";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { diseaseData } from "./data/dummyData";
import { useState } from "react";

function App() {
  const [selectedRegion, setSelectedRegion] =
  useState(diseaseData[0]);

const riskLevel =
  selectedRegion.reportedCases > 350
    ? "CRITICAL"
    : selectedRegion.reportedCases > 250
    ? "HIGH"
    : selectedRegion.reportedCases > 150
    ? "MODERATE"
    : "LOW";
  const data = [
  { day: "Mon", cases: 2400 },
  { day: "Tue", cases: 3200 },
  { day: "Wed", cases: 2900 },
  { day: "Thu", cases: 4100 },
  { day: "Fri", cases: 5200 },
  { day: "Sat", cases: 6100 },
  { day: "Sun", cases: 7200 },
];
  return (
    <div className="app">
      <div className="topbar">
        <div>
          <h1>GLOBAL EPIDEMIC SURVEILLANCE SYSTEM</h1>
          <p>
            AI-powered outbreak intelligence dashboard
          </p>
        </div>

        <div className={`status-box ${riskLevel.toLowerCase()}`}>
  {riskLevel} RISK • LIVE MONITORING
</div>
      </div>

      <div className="main-layout">

<div className="glass-card">
  <h2>Threat Level</h2>

  <div className={`threat-circle ${riskLevel.toLowerCase()}`}>
  <span>{riskLevel}</span>
</div>
<div className="risk-bar-container">

  <div
    className={`risk-bar-fill ${riskLevel.toLowerCase()}`}
    style={{
      width: `${Math.min(
        selectedRegion.reportedCases / 5,
        100
      )}%`
    }}
  ></div>

</div>

<div className="risk-percentage">
  Severity Score:
  {" "}
  {Math.min(
    Math.floor(selectedRegion.reportedCases / 5),
    100
  )}%
</div>
  <div className="risk-stats">

    <div className="risk-item">
      <span>Region</span>
      <strong>{selectedRegion.region}</strong>
    </div>

    <div className="risk-item">
      <span>Cases</span>
      <strong>{selectedRegion.reportedCases}</strong>
    </div>

    <div className="risk-item">
      <span>Humidity</span>
      <strong>{selectedRegion.humidity}%</strong>
    </div>

  </div>
</div>

        <div className="glass-card">
          <h2>Outbreak Analytics</h2>
          <select
  className="region-select"
  onChange={(e) => {
    const region = diseaseData.find(
      item => item.region === e.target.value
    );

    setSelectedRegion(region);
  }}
>
  {diseaseData.map((item, index) => (
    <option key={index}>
      {item.region}
    </option>
  ))}
</select>

          <div className="real-chart">
  <ResponsiveContainer width="100%" height={320}>
    <AreaChart data={data}>

      <defs>
        <linearGradient
          id="casesGradient"
          x1="0"
          y1="0"
          x2="0"
          y2="1"
        >
          <stop
            offset="5%"
            stopColor={
  riskLevel === "LOW"
    ? "#00ffaa"
    : riskLevel === "MODERATE"
    ? "#facc15"
    : riskLevel === "HIGH"
    ? "#fb7185"
    : "#ff00aa"
}
            stopOpacity={0.5}
          />

          <stop
            offset="95%"
            stopColor={
  riskLevel === "LOW"
    ? "#00ffaa"
    : riskLevel === "MODERATE"
    ? "#facc15"
    : riskLevel === "HIGH"
    ? "#fb7185"
    : "#ff00aa"
}
            stopOpacity={0}
          />
        </linearGradient>
      </defs>

      <CartesianGrid
        strokeDasharray="3 3"
        stroke="rgba(255,255,255,0.08)"
      />

      <XAxis
        dataKey="day"
        stroke="#94a3b8"
      />

      <YAxis
        stroke="#94a3b8"
      />

      <Tooltip
        contentStyle={{
          background: "#081120",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "14px",
          color: "white",
        }}
      />

      <Area
        type="monotone"
        dataKey="cases"
        stroke={
  riskLevel === "LOW"
    ? "#00ffaa"
    : riskLevel === "MODERATE"
    ? "#facc15"
    : riskLevel === "HIGH"
    ? "#fb7185"
    : "#ff00aa"
}
        strokeWidth={4}
        fill="url(#casesGradient)"
      />

    </AreaChart>
  </ResponsiveContainer>
</div>
<div className="metrics-grid">

  <div className="metric-card">
    <h3>Temperature</h3>
    <p>{selectedRegion.temperature}°C</p>
  </div>

  <div className="metric-card">
    <h3>Humidity</h3>
    <p>{selectedRegion.humidity}%</p>
  </div>

  <div className="metric-card">
    <h3>Search Trend</h3>
    <p>{selectedRegion.searchTrend}</p>
  </div>

  <div className="metric-card">
    <h3>Reported Cases</h3>
    <p>{selectedRegion.reportedCases}</p>
  </div>

</div>
        </div>

        <div className={`glass-card insights-card ${riskLevel.toLowerCase()}`}>
          <h2>AI Insights</h2>
          <div className="activity-feed">

  <div className="activity-item">
    <div className="activity-dot"></div>
    <p>Scanning environmental anomalies...</p>
  </div>

  <div className="activity-item">
    <div className="activity-dot"></div>
    <p>Analyzing outbreak acceleration trends...</p>
  </div>

  <div className="activity-item">
    <div className="activity-dot"></div>
    <p>Synchronizing regional climate data...</p>
  </div>

</div>

          <div className="insight">
  {selectedRegion.searchTrend > 80
    ? "Public search activity indicates rising outbreak concern."
    : "Search behavior remains within normal thresholds."}
</div>

<div className="insight">
  {selectedRegion.humidity > 70
    ? "High humidity may accelerate vector-borne transmission."
    : "Humidity conditions remain relatively stable."}
</div>

<div className="insight">
  {selectedRegion.reportedCases > 300
    ? "AI model predicts elevated outbreak expansion risk."
    : "Outbreak growth currently appears manageable."}
</div>
        </div>

      </div>
    </div>
  );
}

export default App;