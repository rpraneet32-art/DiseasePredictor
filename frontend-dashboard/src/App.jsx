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

import { useState } from "react";
import Select from "react-select";
import { Download, Lock, LogOut } from "lucide-react";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const [selectedDisease, setSelectedDisease] = useState("Dengue");
  const [selectedRegion, setSelectedRegion] = useState("Maharashtra");
  const [selectedDate, setSelectedDate] = useState("2018-06-15");
  
  const [predictionData, setPredictionData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState("");

  const activeRegions = ["Maharashtra", "Karnataka", "Kerala"];
  const diseases = ["Dengue", "Flu", "Covid"];

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setPredictionData(null);
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
        body: JSON.stringify({ region: selectedRegion, date: selectedDate }),
      });

      const predResult = await predResponse.json();

      if (predResponse.ok) {
        setPredictionData(predResult.data);
      } else {
        setApiError(predResult.message || "Prediction failed.");
        setPredictionData(null);
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
      }else {
        setHistoricalData([]);
      }
    } catch (err) {
      setApiError("Backend connection lost. Check Flask server.");
      setPredictionData(null);
      setHistoricalData([]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadDataset = () => {
    const exportUrl = `http://localhost:5000/api/export/${selectedRegion}`;
    window.open(exportUrl, "_blank");
  };

  const customSelectStyles = {
    control: (provided) => ({
      ...provided,
      background: "#0f172a",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: "16px",
      minHeight: "52px",
      boxShadow: "none",
      color: "white",
    }),
    menu: (provided) => ({
      ...provided,
      background: "#0f172a",
      borderRadius: "16px",
      overflow: "hidden",
      zIndex: 9999,
    }),
    menuList: (provided) => ({
      ...provided,
      background: "#0f172a",
      maxHeight: "240px",
    }),
    option: (provided, state) => ({
      ...provided,
      background: state.isFocused ? "rgba(0,255,170,0.12)" : "#0f172a",
      color: "white",
      cursor: "pointer",
    }),
    singleValue: (provided) => ({
      ...provided,
      color: "white",
    }),
    input: (provided) => ({
      ...provided,
      color: "white",
    }),
  };

  if (!token) {
    return (
      <div className="app">
        <div className="background-grid"></div>
        <div className="particles">
          <span></span><span></span><span></span><span></span><span></span><span></span>
        </div>

        <div className="login-container">
          <div className="glass-card login-card">
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

            <form onSubmit={handleLogin}>
              <input
                type="text"
                placeholder="Username"
                className="login-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              <input
                type="password"
                placeholder="Password"
                className="login-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button type="submit" className="login-btn" disabled={isLoggingIn}>
                {isLoggingIn ? "AUTHENTICATING..." : "INITIALIZE CONNECTION"}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  const currentRisk = predictionData?.risk?.toUpperCase() || "STANDBY";
  const riskColorHex = 
    currentRisk === "LOW" ? "#00ffaa" : 
    currentRisk === "MEDIUM" ? "#facc15" : 
    currentRisk === "HIGH" ? "#fb7185" : "#94a3b8";

  return (
    <div className="app">
      <div className="ticker-wrap">
        <div className="ticker">
          <span>
            ⚠ AI ALERT: Live disease surveillance active • Environmental risk
            patterns detected • AI outbreak forecasting operational • Regional
            health monitoring synchronized •
          </span>
        </div>
      </div>

      <div className="particles">
        <span></span><span></span><span></span><span></span><span></span><span></span>
      </div>

      <div className="topbar">
        {/* TITLE & ACTIONS */}
        <div>
          <h1>Disease Detection Dashboard</h1>
          <p>AI-powered outbreak intelligence dashboard</p>
          
          <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
            <button className="download-btn" onClick={downloadDataset} style={{ marginTop: 0 }}>
              <Download size={18} /> Download CSV
            </button>
            <button className="download-btn logout-btn" onClick={logout} style={{ marginTop: 0 }}>
              <LogOut size={18} /> Logout
            </button>
          </div>
        </div>

        {/* STATUS */}
        <div className={`status-box`} style={{ borderColor: riskColorHex, color: riskColorHex, background: `${riskColorHex}15` }}>
          {currentRisk} RISK • LIVE MONITORING
        </div>
      </div>
      {apiError && <div className="login-error" style={{ position: "relative", zIndex: 10 }}>{apiError}</div>}

      <div className="main-layout">
        <div className="glass-card">
          
          {/* --- CONTROL CENTER START --- */}
          <div style={{ marginBottom: "32px", paddingBottom: "24px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
            <h2 style={{ marginBottom: "20px" }}>Control Center</h2>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              
              {/* DATE PICKER */}
              <input
                type="date"
                className="date-picker"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min="2016-01-01"
                max="2020-12-31"
              />

              {/* DISEASE DROPDOWN (Forced to Top Layer) */}
              <div className="search-select" style={{ position: "relative", zIndex: 50 }}>
                <Select
                  styles={customSelectStyles}
                  options={diseases.map((d) => ({ value: d, label: d }))}
                  value={{ value: selectedDisease, label: selectedDisease }}
                  onChange={(s) => setSelectedDisease(s.value)}
                  placeholder="Disease..."
                />
              </div>

              {/* REGION DROPDOWN (Forced to Lower Layer) */}
              <div className="search-select" style={{ position: "relative", zIndex: 40 }}>
                <Select
                  styles={customSelectStyles}
                  options={activeRegions.map((r) => ({ value: r, label: r }))}
                  value={{ value: selectedRegion, label: selectedRegion }}
                  onChange={(s) => setSelectedRegion(s.value)}
                  placeholder="Region..."
                />
              </div>

              {/* EXECUTE BUTTON */}
              <button className="execute-btn" onClick={executeAnalysis} disabled={isAnalyzing}>
                {isAnalyzing ? "ANALYZING..." : "RUN ANALYSIS"}
              </button>
              
            </div>
          </div>
          {/* --- CONTROL CENTER END --- */}

          {/* --- THREAT LEVEL METRICS --- */}
          <h2>Threat Level</h2>

          <div className="threat-circle" style={{ borderColor: riskColorHex, color: riskColorHex, boxShadow: `0 0 30px ${riskColorHex}80` }}>
            <span>{currentRisk}</span>
          </div>

          <div className="risk-bar-container">
            <div
              className="risk-bar-fill"
              style={{ width: `${predictionData?.probability || 0}%`, background: riskColorHex, boxShadow: `0 0 18px ${riskColorHex}` }}
            ></div>
          </div>

          <div className="risk-percentage">
            AI Confidence: {predictionData?.probability || 0}%
          </div>

          <div className="risk-stats">
            <div className="risk-item">
              <span>Region</span>
              <strong>{predictionData?.region || "---"}</strong>
            </div>
            <div className="risk-item">
              <span>Target Date</span>
              <strong>{predictionData?.date || "---"}</strong>
            </div>
            <div className="risk-item">
              <span>Model Timestamp</span>
              <strong>{predictionData?.timestamp ? new Date(predictionData.timestamp).toLocaleTimeString() : "---"}</strong>
            </div>
          </div>
        </div>
        <div className="glass-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
             <h2>Outbreak Analytics</h2>
          </div>

          <div className="real-chart" style={{ marginTop: '20px' }}>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={historicalData}>
                <defs>
                  <linearGradient id="casesGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={riskColorHex} stopOpacity={0.5} />
                    <stop offset="95%" stopColor={riskColorHex} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    background: "#081120",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "14px",
                    color: "white",
                  }}
                />
                <Area type="monotone" dataKey="cases" stroke={riskColorHex} strokeWidth={4} fill="url(#casesGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Avg Temperature</h3>
              <p>{predictionData?.temperature || "0.0"}°C</p>
            </div>
            <div className="metric-card">
              <h3>Avg Humidity</h3>
              <p>{predictionData?.humidity || "0.0"}%</p>
            </div>
            <div className="metric-card">
              <h3>Search Trend Score</h3>
              <p>{predictionData?.searchTrend || 0}</p>
            </div>
            <div className="metric-card">
              <h3>Risk Multiplier</h3>
              <p>{predictionData ? (predictionData.probability / 10).toFixed(1) : "0.0"}x</p>
            </div>
          </div>
        </div>

        <div className="glass-card insights-card" style={{ borderColor: `${riskColorHex}50` }}>
          <h2>AI Insights</h2>

          <div className="activity-feed">
            <div className="activity-item">
              <div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div>
              <p>Fetching contextual data from MongoDB cluster...</p>
            </div>
            <div className="activity-item">
              <div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div>
              <p>Passing {predictionData?.region || "data"} arrays into baseline_model.pkl...</p>
            </div>
            <div className="activity-item">
              <div className="activity-dot" style={{ background: riskColorHex, boxShadow: `0 0 14px ${riskColorHex}` }}></div>
              <p>Executing Random Forest classification trees...</p>
            </div>
          </div>

          <div className="system-health">
            <h3>System Health</h3>
            <div className="health-item">
              <span>Flask API Connection</span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
            <div className="health-item">
              <span>MongoDB Atlas Link</span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
            <div className="health-item">
              <span>Scikit-Learn Engine</span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
          </div>
          {predictionData && (
            <div style={{ marginTop: "24px" }}>
              <div className="insight">
                {predictionData.humidity > 70
                  ? "High humidity may accelerate disease spread."
                  : "Humidity conditions remain relatively stable."}
              </div>
              <div className="insight">
                {predictionData.probability > 50
                  ? "AI model predicts elevated outbreak expansion risk."
                  : "Outbreak growth currently appears manageable."}
              </div>
              <div className="insight">
                {predictionData.searchTrend > 7
                  ? "Public search activity indicates rising concern."
                  : "Search behavior remains within normal thresholds."}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;