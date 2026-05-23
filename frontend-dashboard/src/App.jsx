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
import Select from "react-select";

import { Download } from "lucide-react";

function App() {

  const [selectedDisease, setSelectedDisease]
  = useState("Dengue");

  const diseaseRegions = [

    ...new Set(

      diseaseData
        .filter(
          item =>
            item.disease === selectedDisease
        )
        .map(
          item => item.region
        )

    )

  ];

  const [selectedRegion, setSelectedRegion]
  = useState("Mumbai");



  const filteredData = diseaseData.filter(
    item =>
      item.disease === selectedDisease &&
      item.region === selectedRegion
  );
  const latestData =
  filteredData[filteredData.length - 1] || {};  




  const totalCases =
    filteredData.reduce(
      (sum, item) =>
        sum + item.reportedCases,
      0
    );



  const riskLevel =
    totalCases > 350
      ? "CRITICAL"
      : totalCases > 220
      ? "HIGH"
      : totalCases > 120
      ? "MODERATE"
      : "LOW";



  const data = filteredData.map(
    item => ({
      day: `W${item.week}`,
      cases: item.reportedCases
    })
  );

const [sortOrder, setSortOrder]
= useState("high");
const downloadDataset = () => {

  const jsonData =
    JSON.stringify(
      filteredData,
      null,
      2
    );

  const blob =
    new Blob(
      [jsonData],
      { type:"application/json" }
    );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    `${selectedDisease}-${selectedRegion}-dataset.json`;

  link.click();

};
const customSelectStyles = {

  control:(provided)=>({
    ...provided,
    background:"#0f172a",
    border:"1px solid rgba(255,255,255,0.08)",
    borderRadius:"16px",
    minHeight:"52px",
    boxShadow:"none",
    color:"white",
  }),

  menu:(provided)=>({
    ...provided,
    background:"#0f172a",
    borderRadius:"16px",
    overflow:"hidden",
    zIndex:9999,
  }),

  menuList:(provided)=>({
    ...provided,
    background:"#0f172a",
    maxHeight:"240px",
  }),

  option:(provided,state)=>({
    ...provided,

    background:state.isFocused
      ? "rgba(0,255,170,0.12)"
      : "#0f172a",

    color:"white",
    cursor:"pointer",
  }),

  singleValue:(provided)=>({
    ...provided,
    color:"white",
  }),

  input:(provided)=>({
    ...provided,
    color:"white",
  }),

  placeholder:(provided)=>({
    ...provided,
    color:"#94a3b8",
  }),

};
  return (

    <div className="app">

      <div className="ticker-wrap">

        <div className="ticker">

          <span>
            ⚠ AI ALERT:
            Live disease surveillance active •
            Environmental risk patterns detected •
            AI outbreak forecasting operational •
            Regional health monitoring synchronized •
          </span>

        </div>

      </div>



      <div className="particles">

        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>

      </div>



      <div className="topbar">

        <Select
  className="search-select"
  classNamePrefix="search"
  maxMenuHeight={240}

  styles={{

    control:(provided)=>({
      ...provided,
      background:"#0f172a",
      border:"1px solid rgba(255,255,255,0.08)",
      borderRadius:"16px",
      minHeight:"52px",
      boxShadow:"none",
      color:"white",
    }),

    menu:(provided)=>({
      ...provided,
      background:"#0f172a",
      borderRadius:"16px",
      overflow:"hidden",
      zIndex:9999,
    }),

    menuList:(provided)=>({
      ...provided,
      background:"#0f172a",
      maxHeight:"240px",
    }),

    option:(provided,state)=>({
      ...provided,
      background:state.isFocused
        ? "rgba(0,255,170,0.12)"
        : "#0f172a",

      color:"white",
      cursor:"pointer",
    }),

    singleValue:(provided)=>({
      ...provided,
      color:"white",
    }),

    input:(provided)=>({
      ...provided,
      color:"white",
    }),

    placeholder:(provided)=>({
      ...provided,
      color:"#94a3b8",
    }),

  }}

  options={
    [...new Set(
      diseaseData.map(
        item => item.disease
      )
    )].map(disease => ({
      value:disease,
      label:disease
    }))
  }

  value={{
    value:selectedDisease,
    label:selectedDisease
  }}

  onChange={(selected)=>{

    setSelectedDisease(selected.value);

    const newRegions =
      diseaseData
        .filter(
          item =>
            item.disease === selected.value
        )
        .map(
          item => item.region
        );

    setSelectedRegion(newRegions[0]);

  }}

  placeholder="Search disease..."
/>



        <div>

          <h1>Disease Detection Dashboard</h1>

          <p>
            AI-powered outbreak intelligence dashboard
          </p>
          <button
  className="download-btn"
  onClick={downloadDataset}
>

  <Download size={18} />

  Download Dataset

</button>

        </div>



        <div
          className={`status-box ${riskLevel.toLowerCase()}`}
        >
          {riskLevel} RISK • LIVE MONITORING
        </div>

      </div>



      <div className="main-layout">



        {/* LEFT PANEL */}



        <div className="glass-card">

          <h2>Threat Level</h2>

          <div
            className={`threat-circle ${riskLevel.toLowerCase()}`}
          >
            <span>{riskLevel}</span>
          </div>



          <div className="risk-bar-container">

            <div
              className={`risk-bar-fill ${riskLevel.toLowerCase()}`}

              style={{
                width: `${Math.min(
                  totalCases / 5,
                  100
                )}%`
              }}
            ></div>

          </div>



          <div className="risk-percentage">

            Severity Score:

            {" "}

            {Math.min(
              Math.floor(totalCases / 5),
              100
            )}%

          </div>



          <div className="risk-stats">

            <div className="risk-item">
              <span>Region</span>
              <strong>{selectedRegion}</strong>
            </div>

            <div className="risk-item">
              <span>Total Cases</span>
              <strong>{totalCases}</strong>
            </div>

            <div className="risk-item">
              <span>Humidity</span>
              <strong>
  {latestData.humidity.toFixed(1)}%
</strong>
            </div>

          </div>



          <div className="region-table">

  <div
    style={{
      display:"flex",
      justifyContent:"space-between",
      alignItems:"center",
      marginBottom:"18px"
    }}
  >

    <h3>Regional Comparison</h3>

    <Select

  className="search-select"

  classNamePrefix="search"

  styles={customSelectStyles}

  isSearchable={false}

  options={[
    {
      value:"high",
      label:"High → Low"
    },
    {
      value:"low",
      label:"Low → High"
    }
  ]}

  value={{
    value:sortOrder,
    label:
      sortOrder === "high"
        ? "High → Low"
        : "Low → High"
  }}

  onChange={(selected)=>
    setSortOrder(selected.value)
  }

/>
  </div>



  <div className="region-row header">
    <span>Region</span>
    <span>Cases</span>
    <span>Risk</span>
  </div>



  {[...diseaseRegions]

    .map(region => {

      const regionData =
        diseaseData.filter(
          item =>
            item.disease === selectedDisease &&
            item.region === region
        );

      const regionTotal =
        regionData.reduce(
          (sum, item) =>
            sum + item.reportedCases,
          0
        );

      const regionRisk =
        regionTotal > 350
          ? "high"
          : regionTotal > 220
          ? "moderate"
          : "low";

      return {
        region,
        regionTotal,
        regionRisk
      };

    })

    .sort((a,b)=>

      sortOrder === "high"
        ? b.regionTotal - a.regionTotal
        : a.regionTotal - b.regionTotal

    )

    .slice(0,5)

    .map(item => (

      <div
        className="region-row"
        key={item.region}
      >

        <span>{item.region}</span>

        <span>{item.regionTotal}</span>

        <span className={item.regionRisk}>
          {item.regionRisk.toUpperCase()}
        </span>

      </div>

    ))}

</div>

        </div>



        {/* CENTER PANEL */}

<div className="glass-card">

  <h2>Outbreak Analytics</h2>

  <Select

    className="search-select"

    classNamePrefix="search"

    styles={customSelectStyles}

    options={
      diseaseRegions.map(region => ({
        value:region,
        label:region
      }))
    }

    value={{
      value:selectedRegion,
      label:selectedRegion
    }}

    onChange={(selected)=>
      setSelectedRegion(
        selected.value
      )
    }

    placeholder="Search region..."

  />

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
          domain={[
            0,
            Math.max(
              ...data.map(
                item => item.cases
              ),
              50
            ) + 20
          ]}
        />

        <Tooltip
          contentStyle={{
            background:"#081120",
            border:
              "1px solid rgba(255,255,255,0.08)",
            borderRadius:"14px",
            color:"white",
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
      <h3>Avg Temperature</h3>

      <p>
        {latestData?.temperature?.toFixed(1) || "0.0"}°C
      </p>
    </div>

    <div className="metric-card">
      <h3>Avg Humidity</h3>

      <p>
        {latestData?.humidity?.toFixed(1) || "0.0"}%
      </p>
    </div>

    <div className="metric-card">
      <h3>Search Trend</h3>

      <p>
        {latestData?.searchTrend || 0}
      </p>
    </div>

    <div className="metric-card">
      <h3>Weekly Cases</h3>

      <p>
        {latestData?.reportedCases || 0}
      </p>
    </div>

  </div>

  <div className="forecast-panel">

    <div className="forecast-header">
      AI Forecast Projection
    </div>

    <div className="forecast-stats">

      <div className="forecast-box">
        <span>24H</span>

        <strong>
          +{Math.floor(
            (latestData?.reportedCases || 0) * 0.08
          )}
        </strong>
      </div>

      <div className="forecast-box">
        <span>3 DAYS</span>

        <strong>
          +{Math.floor(
            (latestData?.reportedCases || 0) * 0.22
          )}
        </strong>
      </div>

      <div className="forecast-box">
        <span>7 DAYS</span>

        <strong>
          +{Math.floor(
            (latestData?.reportedCases || 0) * 0.45
          )}
        </strong>
      </div>

    </div>

  </div>

</div>
        {/* RIGHT PANEL */}



        <div
          className={`glass-card insights-card ${riskLevel.toLowerCase()}`}
        >

          <h2>AI Insights</h2>



          <div className="activity-feed">

            <div className="activity-item">
              <div className="activity-dot"></div>
              <p>
                Monitoring {selectedDisease} transmission trends...
              </p>
            </div>

            <div className="activity-item">
              <div className="activity-dot"></div>
              <p>
                Analyzing environmental outbreak factors...
              </p>
            </div>

            <div className="activity-item">
              <div className="activity-dot"></div>
              <p>
                Synchronizing regional health surveillance...
              </p>
            </div>

          </div>



          <div className="system-health">

            <h3>System Health</h3>



            <div className="health-item">

              <span>AI Processing</span>

              <div className="health-bar">
                <div
                  className="health-fill"
                  style={{ width: "92%" }}
                ></div>
              </div>

            </div>



            <div className="health-item">

              <span>Data Synchronization</span>

              <div className="health-bar">
                <div
                  className="health-fill"
                  style={{ width: "84%" }}
                ></div>
              </div>

            </div>



            <div className="health-item">

              <span>Prediction Confidence</span>

              <div className="health-bar">
                <div
                  className="health-fill"
                  style={{ width: "96%" }}
                ></div>
              </div>

            </div>

          </div>



          <div className="insight">

            {latestData.humidity > 70

              ? "High humidity may accelerate disease spread."

              : "Humidity conditions remain relatively stable."}

          </div>



          <div className="insight">

            {totalCases > 300

              ? "AI model predicts elevated outbreak expansion risk."

              : "Outbreak growth currently appears manageable."}

          </div>



          <div className="insight">

            {latestData.searchTrend > 7

              ? "Public search activity indicates rising concern."

              : "Search behavior remains within normal thresholds."}

          </div>

        </div>



      </div>

    </div>

  );

}

export default App;