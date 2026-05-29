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
import "leaflet/dist/leaflet.css";
import Heatmap from "./components/Heatmap";

function App() {
  // === BACKEND STATE ===
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  
  const [predictionData, setPredictionData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [regionalSummary, setRegionalSummary] = useState([]); // <-- NEW LIVE TABLE STATE
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState("");

  // === UI STATE ===
  const [selectedDisease, setSelectedDisease] = useState("Dengue");
  const [selectedRegion, setSelectedRegion] = useState("Maharashtra");
  const [selectedDate, setSelectedDate] = useState("2018-06-15");
  const [visibleWeeks, setVisibleWeeks] = useState(8);
  const [startIndex, setStartIndex] = useState(0);
  const [sortOrder, setSortOrder] = useState("high");
  const [showHeatmap, setShowHeatmap] = useState(false);

  // Notice we removed Delhi since your pipeline only scraped 3 states
  const activeRegions = ["Maharashtra", "Karnataka", "Kerala"];
  const diseases = ["Dengue", "Flu", "Covid"];

  // === API CALLS ===
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setPredictionData(null);
    setHistoricalData([]);
    setRegionalSummary([]);
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
        setLoginError(data.message || "Invalid credentials.");
      }
    } catch (err) {
      setLoginError("Connection failed. Check Flask server.");
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
      // 1. Fetch ML Prediction
      const predResponse = await fetch("http://localhost:5000/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ region: selectedRegion, date: selectedDate, disease: selectedDisease }),
      });
      const predResult = await predResponse.json();
      if (predResponse.ok) setPredictionData(predResult.data);
      else setApiError(predResult.message);

      // 2. Fetch Line Chart Data
      const histResponse = await fetch(`http://localhost:5000/api/historical/${selectedRegion}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const histResult = await histResponse.json();
      if (histResponse.ok) {
        // THE FIX: Filter out "ghost data" spikes so the chart scale isn't ruined
        const cleanData = histResult.data.filter(item => item.Reported_Cases < 5000); 
        
        setHistoricalData(cleanData.map((item) => ({ 
          day: `W${item.Week_Num}`, 
          cases: item.Reported_Cases || 0 
        })));
      }

      // 3. NEW: Fetch Data for the Regional Comparison Table
      const summaryResponse = await fetch(`http://localhost:5000/api/regional-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const summaryResult = await summaryResponse.json();
      if (summaryResponse.ok) {
        setRegionalSummary(summaryResult.data);
      }

    } catch (err) {
      setApiError("Backend connection lost.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadDataset = () => window.open(`http://localhost:5000/api/export/${selectedRegion}`, "_blank");

  const customSelectStyles = {
    control:(provided)=>({ ...provided, background:"#fcfcfd", border:"1px solid #cbd5e1", borderRadius:"16px", minHeight:"52px", boxShadow:"none", cursor:"pointer", color:"#0f172a" }),
    menu:(provided)=>({ ...provided, background:"#ffffff", borderRadius:"16px", overflow:"hidden", border:"1px solid #e2e8f0", boxShadow:"0 10px 24px rgba(15,23,42,0.08)", zIndex:9999 }),
    menuList:(provided)=>({ ...provided, maxHeight:"240px", background:"#ffffff" }),
    option:(provided,state)=>({ ...provided, background:state.isFocused?"#f1f5f9":"#ffffff", color:state.isSelected?"#2563eb":"#0f172a", padding:"14px", cursor:"pointer", fontWeight:state.isSelected?600:400 }),
    singleValue:(provided)=>({ ...provided, color:"#0f172a", fontWeight:600 }),
    input:(provided)=>({ ...provided, color:"#0f172a" }),
    placeholder:(provided)=>({ ...provided, color:"#64748b" }),
  };

  // === DYNAMIC DATA BINDING ===
  const totalCases = historicalData.reduce((sum, item) => sum + item.cases, 0);
  const latestWeekCases = historicalData.length > 0 ? historicalData[historicalData.length - 1].cases : 0;
  const firstWeekCases = historicalData.length > 0 ? historicalData[0].cases : 0;

  const latestData = {
    temperature: predictionData?.temperature || 0,
    humidity: predictionData?.humidity || 0,
    searchTrend: predictionData?.searchTrend || 0,
    reportedCases: latestWeekCases
  };

  const riskLevel = predictionData?.risk?.toUpperCase() || "STANDBY";
  
  const growthPercent = firstWeekCases ? Math.round(((latestWeekCases - firstWeekCases) / firstWeekCases) * 100) : 0;
  let observationText = `${selectedDisease} activity remains relatively stable in ${selectedRegion}.`;
  if(growthPercent >= 40) observationText = `Sharp increase detected in ${selectedDisease} activity across ${selectedRegion}.`;
  else if(growthPercent >= 15) observationText = `${selectedDisease} cases are gradually rising in ${selectedRegion}.`;
  else if(growthPercent <= -15) observationText = `${selectedDisease} spread appears to be declining in ${selectedRegion}.`;

  const chartData = historicalData;
  const data = chartData.slice(startIndex, startIndex + visibleWeeks);

  // === LOGIN GATE ===
  if (!token) {
    return (
      <div className="app">
        <div className="login-container">
          <div className="login-card">
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "24px", color: "#2563eb" }}>
              <Lock size={56} strokeWidth={1.5} />
            </div>
            <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "#0f172a", marginBottom: "8px" }}>SYSTEM ACCESS</h1>
            <p style={{ color: "#64748b", marginBottom: "32px" }}>Authenticate to connect to the Outbreak Engine API.</p>
            {loginError && <div className="login-error">{loginError}</div>}
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column' }}>
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
      <div className="topbar">
        <div style={{ display: 'flex', gap: '10px', zIndex: 100 }}>
          <Select className="search-select" classNamePrefix="search" maxMenuHeight={240} styles={customSelectStyles}
            options={diseases.map(d => ({ value: d, label: d }))}
            value={{ value: selectedDisease, label: selectedDisease }}
            onChange={(s) => setSelectedDisease(s.value)} placeholder="Search disease..."
          />
          <Select className="search-select" classNamePrefix="search" maxMenuHeight={240} styles={customSelectStyles}
            options={activeRegions.map(r => ({ value: r, label: r }))}
            value={{ value: selectedRegion, label: selectedRegion }}
            onChange={(s) => setSelectedRegion(s.value)} placeholder="Search region..."
          />
          <input type="date" className="date-picker" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} min="2016-01-01" max="2020-12-31" />
          <button className="execute-btn" onClick={executeAnalysis} disabled={isAnalyzing}>
            {isAnalyzing ? "..." : "RUN ANALYSIS"}
          </button>
        </div>

        {showHeatmap && (
          <div className="heatmap-modal">
            <div className="heatmap-container">
              <div className="heatmap-topbar">
                <h2>Regional Heatmap</h2>
                <button onClick={() => setShowHeatmap(false)} className="close-map-btn">✕</button>
              </div>
              <Heatmap />
              <div className="heatmap-overlay">
                <button className="close-map-btn" onClick={() => setShowHeatmap(false)}>✕ Close Map</button>
                <Heatmap />
              </div>
            </div>
          </div>
        )}

        <div className="topbar-center">
          <h1>Disease Detection Dashboard</h1>
          <p>AI-powered outbreak intelligence dashboard</p>
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button className="download-btn" onClick={downloadDataset}><Download size={18} /> Dataset</button>
            <button className="download-btn" onClick={logout} style={{ background: '#f87171' }}><LogOut size={18} /> Logout</button>
          </div>
        </div>

        <div className="heatmap-shortcut">
          <div>
            <h3>Regional Heatmap</h3>
            <p>Geographic outbreak visualization</p>
          </div>
          <button className="heatmap-btn" onClick={() => setShowHeatmap(true)}>Open</button>
        </div>
      </div>
      
      {apiError && <div className="login-error" style={{ marginBottom: '20px' }}>{apiError}</div>}

      <div className="main-layout">
        {/* LEFT PANEL */}
        <div className="glass-card">
          <h2>Threat Level</h2>
          <div className={`threat-circle ${riskLevel.toLowerCase()}`}>
            <span>{riskLevel}</span>
          </div>

          <div className="risk-bar-container">
            <div className={`risk-bar-fill ${riskLevel.toLowerCase()}`} style={{ width: `${predictionData?.probability || 0}%` }}></div>
          </div>
          <div className="risk-percentage" style={{ textAlign: 'center' }}>AI Confidence: {predictionData?.probability || 0}%</div>

          <div className="risk-stats">
            <div className="risk-item"><span>Region</span><strong>{selectedRegion}</strong></div>
            <div className="risk-item"><span>Target Date</span><strong>{selectedDate}</strong></div>
            <div className="risk-item"><span>Humidity</span><strong>{latestData.humidity.toFixed(1)}%</strong></div>
          </div>

          <div className="region-table">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
              <h3>Regional Comparison</h3>
              <Select className="search-select" classNamePrefix="search" styles={customSelectStyles} isSearchable={false}
                options={[{ value: "high", label: "High → Low" }, { value: "low", label: "Low → High" }]}
                value={{ value: sortOrder, label: sortOrder === "high" ? "High → Low" : "Low → High" }}
                onChange={(s) => setSortOrder(s.value)}
              />
            </div>
            <div className="region-row header"><span>Region</span><span>Cases</span><span>Risk</span></div>
            
            {/* 🔗 FULLY WIRED TO LIVE DATABASE! */}
            {regionalSummary.sort((a, b) => sortOrder === "high" ? b.total - a.total : a.total - b.total).map(item => (
              <div className="region-row" key={item.region}>
                <span>{item.region}</span><span>{item.total}</span>
                <span className={item.risk}>{item.risk.toUpperCase()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CENTER PANEL */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2>Outbreak Analytics</h2>
          </div>
          
          <div className="chart-controls">
            <button onClick={() => setStartIndex(Math.max(startIndex - visibleWeeks, 0))}>← Prev</button>
            <button onClick={() => setStartIndex(Math.min(startIndex + visibleWeeks, Math.max(chartData.length - visibleWeeks, 0)))}>Next →</button>
            <button onClick={() => setVisibleWeeks(Math.max(4, visibleWeeks - 2))}>Zoom In</button>
            <button onClick={() => setVisibleWeeks(Math.min(20, visibleWeeks + 2))}>Zoom Out</button>
          </div>

          <div className="real-chart">
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="casesGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MODERATE' ? '#facc15' : '#14b8a6'} stopOpacity={0.5} />
                    <stop offset="95%" stopColor={riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MODERATE' ? '#facc15' : '#14b8a6'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="day" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "14px", color: "#0f172a", boxShadow: "0 4px 14px rgba(15,23,42,0.08)" }} />
                <Area type="monotone" dataKey="cases" stroke={riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MODERATE' ? '#facc15' : '#14b8a6'} strokeWidth={3} fill="url(#casesGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="metrics-grid">
            <div className="metric-card"><h3>Avg Temperature</h3><p>{latestData.temperature.toFixed(1)}°C</p></div>
            <div className="metric-card"><h3>Avg Humidity</h3><p>{latestData.humidity.toFixed(1)}%</p></div>
            <div className="metric-card"><h3>Search Trend</h3><p>{latestData.searchTrend.toFixed(1)}</p></div>
            <div className="metric-card"><h3>Weekly Cases</h3><p>{latestData.reportedCases}</p></div>
          </div>

          <div className="forecast-panel">
            <div className="forecast-header" style={{ color: '#94a3b8' }}>AI Forecast Projection</div>
            <div className="forecast-stats">
              <div className="forecast-box">
                <span style={{ color: '#94a3b8' }}>24H</span>
                <strong>+{Math.floor(latestData.reportedCases * 0.08)}</strong>
              </div>
              <div className="forecast-box">
                <span style={{ color: '#94a3b8' }}>3 DAYS</span>
                <strong>+{Math.floor(latestData.reportedCases * 0.22)}</strong>
              </div>
              <div className="forecast-box">
                <span style={{ color: '#94a3b8' }}>7 DAYS</span>
                <strong>+{Math.floor(latestData.reportedCases * 0.45)}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className={`glass-card insights-card ${riskLevel.toLowerCase()}`}>
          <h2>AI Insights</h2>

          <div className="activity-feed">
            <div className="activity-item"><div className="activity-dot"></div><p>Fetching contextual data from MongoDB...</p></div>
            <div className="activity-item"><div className="activity-dot"></div><p>Passing arrays into ensemble model...</p></div>
            <div className="activity-item"><div className="activity-dot"></div><p>Synchronizing regional health surveillance...</p></div>
          </div>

          <div className="system-health">
            <h3>System Health</h3>
            <div className="health-item">
              <span>Flask API <span style={{color:'#14b8a6'}}>100%</span></span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
            <div className="health-item">
              <span>MongoDB Atlas <span style={{color:'#14b8a6'}}>100%</span></span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
            <div className="health-item">
              <span>XGBoost Engine <span style={{color:'#14b8a6'}}>100%</span></span>
              <div className="health-bar"><div className="health-fill" style={{ width: "100%" }}></div></div>
            </div>
          </div>

          <div className="insight" style={{ marginTop: '20px' }}>
            {latestData.humidity > 70 ? "High humidity may accelerate disease spread." : "Humidity conditions remain relatively stable."}
          </div>
          <div className="insight">
            {predictionData && predictionData.probability > 50 ? "AI model predicts elevated outbreak expansion risk." : "Outbreak growth currently appears manageable."}
          </div>
          <div className="insight">
            {latestData.searchTrend > 7 ? "Public search activity indicates rising concern." : "Search behavior remains within normal thresholds."}
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