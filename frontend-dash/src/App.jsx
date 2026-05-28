import "./App.css";
import CountUp from "react-countup";
import { motion } from "framer-motion";
import { FaExclamationTriangle, FaHeartbeat, FaShieldVirus, FaBiohazard } from "react-icons/fa";
import { useState } from "react";
import Select from "react-select";
import { Download, Lock, LogOut } from "lucide-react";
import "leaflet/dist/leaflet.css";
import Heatmap from "./components/Heatmap";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [apiError, setApiError] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [selectedDisease, setSelectedDisease] = useState("Dengue");
  const [selectedRegion, setSelectedRegion] = useState("Maharashtra");
  const [selectedDate, setSelectedDate] = useState("2018-06-15");

  const [predictionData, setPredictionData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);

  const [visibleWeeks, setVisibleWeeks] = useState(8);
  const [startIndex, setStartIndex] = useState(0);
  const [showHeatmap, setShowHeatmap] = useState(false);

  const activeRegions = ["Maharashtra", "Karnataka", "Kerala", "Delhi"];
  const diseases = ["Dengue", "Flu", "Covid"];

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setPredictionData(null);
    setHistoricalData([]);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError("");

    try {
      const response = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.token);
        setToken(data.token);
      } else {
        setLoginError(data.message || "Invalid security credentials.");
      }
    } catch (err) {
      setLoginError("Connection failed. Is the Flask backend running?");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const executeAnalysis = async () => {
    setIsAnalyzing(true);
    setApiError("");
    setPredictionData(null); 
    setHistoricalData([]);

    try {
      const predResponse = await fetch("http://localhost:5000/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ region: selectedRegion, date: selectedDate, disease: selectedDisease }),
      });

      const predResult = await predResponse.json();
      if (predResponse.ok) {
        setPredictionData(predResult.data);
      } else {
        setApiError(predResult.message || "Prediction failed.");
      }

      const histResponse = await fetch(`http://localhost:5000/api/historical/${selectedRegion}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const histResult = await histResponse.json();
      if (histResponse.ok) {
        const formattedData = histResult.data.map((item) => ({
          day: `W${item.Week_Num}`,
          cases: item.Reported_Cases || 0,
        }));
        setHistoricalData(formattedData);
      }
    } catch (err) {
      setApiError("Backend connection lost. Check Flask server.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadDataset = () => {
    window.open(`http://localhost:5000/api/export/${selectedRegion}`, "_blank");
  };

  const customSelectStyles = {
    control: (provided) => ({ ...provided, background: "#0f172a", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", minHeight: "52px", boxShadow: "none", color: "white" }),
    menu: (provided) => ({ ...provided, background: "#0f172a", borderRadius: "16px", overflow: "hidden", zIndex: 9999 }),
    menuList: (provided) => ({ ...provided, background: "#0f172a", maxHeight: "240px" }),
    option: (provided, state) => ({ ...provided, background: state.isFocused ? "rgba(0,255,170,0.12)" : "#111827", color: "white", cursor: "pointer" }),
    singleValue: (provided) => ({ ...provided, color: "white" }),
    input: (provided) => ({ ...provided, color: "white" }),
    placeholder: (provided) => ({ ...provided, color: "#94a3b8" }),
  };

  const chartData = historicalData;
  const data = chartData.slice(startIndex, startIndex + visibleWeeks);

  const latestWeekCases = historicalData.length > 0 ? historicalData[historicalData.length - 1].cases : 0;
  const firstWeekCases = historicalData.length > 0 ? historicalData[0].cases : 0;

  const latestData = {
    temperature: predictionData?.temperature || 0,
    humidity: predictionData?.humidity || 0,
    searchTrend: predictionData?.searchTrend || 0,
    reportedCases: latestWeekCases
  };

  const riskLevel = predictionData?.risk?.toUpperCase() || "STANDBY";
  const riskColorHex = 
    riskLevel === "LOW" ? "#00ffaa" : 
    riskLevel === "MEDIUM" ? "#facc15" : 
    riskLevel === "HIGH" ? "#fb7185" : "#94a3b8";

  const growthPercent = firstWeekCases ? Math.round(((latestWeekCases - firstWeekCases) / firstWeekCases) * 100) : 0;
  let observationText = `${selectedDisease} activity remains relatively stable in ${selectedRegion}.`;
  if(growthPercent >= 40) observationText = `Sharp increase detected in ${selectedDisease} activity across ${selectedRegion}.`;
  else if(growthPercent >= 15) observationText = `${selectedDisease} cases are gradually rising in ${selectedRegion}.`;
  else if(growthPercent <= -15) observationText = `${selectedDisease} spread appears to be declining in ${selectedRegion}.`;

  if (!token) {
    return (
      <div className="app">
        <div className="background-grid"></div>
        <div className="login-container">
          <div className="glass-card login-card" style={{ maxWidth: '440px', margin: 'auto', marginTop: '10vh' }}>
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "24px", color: "#00ffaa" }}>
              <Lock size={56} strokeWidth={1.5} />
            </div>
            <h1 style={{ fontSize: "2.2rem", fontWeight: 900, letterSpacing: "-1px", marginBottom: "8px" }}>
              SYSTEM ACCESS
            </h1>
            <p style={{ color: "#94a3b8", marginBottom: "32px", fontSize: "0.95rem" }}>
              Authenticate to connect to the Outbreak Engine API.
            </p>
            {loginError && <div className="login-error">{loginError}</div>}
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input type="text" placeholder="Username" className="login-input" value={username} onChange={(e) => setUsername(e.target.value)} required />
              <input type="password" placeholder="Password" className="login-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
              <button type="submit" className="login-btn" disabled={isLoggingIn}>
                {isLoggingIn ? "AUTHENTICATING..." : "INITIALIZE CONNECTION"}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="app">
      <div className="background-grid"></div>

      <header className="topbar" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '12px', zIndex: 50 }}>
            <Select className="search-select" styles={customSelectStyles} options={diseases.map(d => ({ value: d, label: d }))} value={{ value: selectedDisease, label: selectedDisease }} onChange={(s) => setSelectedDisease(s.value)} placeholder="Disease..." />
            <Select className="search-select" styles={customSelectStyles} options={activeRegions.map(r => ({ value: r, label: r }))} value={{ value: selectedRegion, label: selectedRegion }} onChange={(s) => setSelectedRegion(s.value)} placeholder="Region..." />
            <input type="date" className="date-picker" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} min="2016-01-01" max="2020-12-31" />
            <button className="execute-btn" onClick={executeAnalysis} disabled={isAnalyzing}>
              {isAnalyzing ? "ANALYZING..." : "RUN ANALYSIS"}
            </button>
        </div>

        <div className="topbar-center" style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <h1 style={{ fontSize: '1.8rem', margin: 0 }}>EPIDEMIC SURVEILLANCE</h1>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '12px' }}>
              <button className="download-btn" onClick={downloadDataset} style={{ padding: '8px 16px', background: '#f1f5f9', color: '#0f172a' }}>
                <Download size={16} /> CSV
              </button>
              <button className="download-btn logout-btn" onClick={logout} style={{ padding: '8px 16px', background: '#fee2e2', color: '#ef4444' }}>
                <LogOut size={16} /> Logout
              </button>
          </div>
        </div>
      </header>

      {showHeatmap && (
        <div className="heatmap-modal">
          <div className="heatmap-container">
            <div className="heatmap-topbar">
              <h2>Regional Heatmap</h2>
              <button onClick={() => setShowHeatmap(false)} className="close-map-btn">✕</button>
            </div>
            <Heatmap />
          </div>
        </div>
      )}

      {apiError && <div className="login-error" style={{ position: "relative", zIndex: 10 }}>{apiError}</div>}

      <div className="main-layout">
        {/* LEFT PANEL */}
        <div className="glass-card">
          <h2>Threat Level</h2>
          <div className="threat-circle" style={{ borderColor: riskColorHex, color: riskColorHex, boxShadow: `0 0 30px ${riskColorHex}80` }}>
            <span>{riskLevel}</span>
          </div>

          <div className="risk-bar-container">
            <div className="risk-bar-fill" style={{ width: `${predictionData?.probability || 0}%`, background: riskColorHex, boxShadow: `0 0 18px ${riskColorHex}` }}></div>
          </div>

          <div className="risk-percentage">AI Confidence: {predictionData?.probability || 0}%</div>

          <div className="risk-stats">
            <div className="risk-item"><span>Region</span><strong>{predictionData?.region || "---"}</strong></div>
            <div className="risk-item"><span>Target Date</span><strong>{predictionData?.date || "---"}</strong></div>
            <div className="risk-item"><span>Timestamp</span><strong>{predictionData?.timestamp ? new Date(predictionData.timestamp).toLocaleTimeString() : "---"}</strong></div>
          </div>
          
          <button className="execute-btn" style={{ width: '100%', marginTop: '24px', background: '#0f766e' }} onClick={() => setShowHeatmap(true)}>
             Open Geographic Heatmap
          </button>
        </div>

        {/* CENTER PANEL */}
        <div className="glass-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2>Outbreak Analytics</h2>
            <div className="chart-controls" style={{ margin: 0 }}>
              <button onClick={() => setStartIndex(Math.max(startIndex - visibleWeeks, 0))}>←</button>
              <button onClick={() => setStartIndex(Math.min(startIndex + visibleWeeks, chartData.length - visibleWeeks))}>→</button>
              <button onClick={() => setVisibleWeeks(Math.max(4, visibleWeeks - 2))}>+</button>
              <button onClick={() => setVisibleWeeks(Math.min(20, visibleWeeks + 2))}>-</button>
            </div>
          </div>

          <div className="real-chart">
            {historicalData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={data}>
                    <defs>
                      <linearGradient id="casesGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={riskColorHex} stopOpacity={0.5} />
                        <stop offset="95%" stopColor={riskColorHex} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="day" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background:"#081120", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"14px", color:"white" }} />
                    <Area type="monotone" dataKey="cases" stroke={riskColorHex} strokeWidth={4} fill="url(#casesGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
            ) : (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                    Run Analysis to view historical timeline.
                </div>
            )}
          </div>

          <div className="metrics-grid">
            <div className="metric-card"><h3>Avg Temp</h3><p>{latestData.temperature.toFixed(1)}°C</p></div>
            <div className="metric-card"><h3>Avg Humidity</h3><p>{latestData.humidity.toFixed(1)}%</p></div>
            <div className="metric-card"><h3>Search Trend</h3><p>{latestData.searchTrend}</p></div>
            <div className="metric-card"><h3>Reported Cases</h3><p>{latestData.reportedCases}</p></div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="glass-card insights-card" style={{ borderColor: `${riskColorHex}50` }}>
          <h2>AI Insights</h2>

          <div className="activity-feed">
            <div className="activity-item"><div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div><p>Fetching contextual data from MongoDB cluster...</p></div>
            <div className="activity-item"><div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div><p>Passing arrays into baseline_model.pkl...</p></div>
            <div className="activity-item"><div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div><p>Executing Random Forest classification trees...</p></div>
          </div>

          <div className="system-health">
            <h3>System Health</h3>
            <div className="health-item"><span>Flask API</span><div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div></div>
            <div className="health-item"><span>MongoDB Atlas</span><div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div></div>
            <div className="health-item"><span>Scikit-Learn Engine</span><div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div></div>
          </div>

          <div className="observation-card">
            <h3>Key Observation</h3>
            <div className="observation-pill">{observationText}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;