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
    filteredData[filteredData.length - 1];



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

        <select
          className="disease-select"

          value={selectedDisease}

          onChange={(e) => {

            const disease = e.target.value;

            setSelectedDisease(disease);

            const newRegions =
              diseaseData
                .filter(
                  item =>
                    item.disease === disease
                )
                .map(
                  item => item.region
                );

            setSelectedRegion(newRegions[0]);

          }}
        >

          {[...new Set(
            diseaseData.map(
              item => item.disease
            )
          )].map(disease => (

            <option
              key={disease}
              value={disease}
            >
              {disease}
            </option>

          ))}

        </select>



        <div>

          <h1>Disease Detection Dashboard</h1>

          <p>
            AI-powered outbreak intelligence dashboard
          </p>

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
              <strong>{latestData.humidity}%</strong>
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

    <select
      className="region-select"

      style={{
        marginBottom:0,
        padding:"8px 12px",
        fontSize:"0.9rem"
      }}

      value={sortOrder}

      onChange={(e)=>
        setSortOrder(e.target.value)
      }
    >

      <option value="high">
        High → Low
      </option>

      <option value="low">
        Low → High
      </option>

    </select>

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



          <select
            className="region-select"

            value={selectedRegion}

            onChange={(e) =>
              setSelectedRegion(e.target.value)
            }
          >

            {diseaseRegions.map(region => (

              <option
                key={region}
                value={region}
              >
                {region}
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
                    border:
                      "1px solid rgba(255,255,255,0.08)",
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
              <p>{latestData.temperature}°C</p>
            </div>

            <div className="metric-card">
              <h3>Humidity</h3>
              <p>{latestData.humidity}%</p>
            </div>

            <div className="metric-card">
              <h3>Search Trend</h3>
              <p>{latestData.searchTrend}</p>
            </div>

            <div className="metric-card">
              <h3>Weekly Cases</h3>
              <p>{latestData.reportedCases}</p>
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
                    latestData.reportedCases * 0.08
                  )}
                </strong>
              </div>



              <div className="forecast-box">
                <span>3 DAYS</span>

                <strong>
                  +{Math.floor(
                    latestData.reportedCases * 0.22
                  )}
                </strong>
              </div>



              <div className="forecast-box">
                <span>7 DAYS</span>

                <strong>
                  +{Math.floor(
                    latestData.reportedCases * 0.45
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