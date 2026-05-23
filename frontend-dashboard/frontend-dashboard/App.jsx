import "./App.css";
import CountUp from "react-countup";
import { motion } from "framer-motion";
import {
  FaExclamationTriangle,
  FaHeartbeat,
  FaShieldVirus,
  FaBiohazard,
} from "react-icons/fa";

function App() {
  const stats = [
    {
      title: "Predicted Cases",
      value: 12480,
      color: "#00ffaa",
    },
    {
      title: "Critical Zones",
      value: 18,
      color: "#ff5c7c",
    },
    {
      title: "Recovery Rate",
      value: 84,
      suffix: "%",
      color: "#4da3ff",
    },
    {
      title: "Transmission Growth",
      value: 12,
      suffix: "%",
      color: "#ffb84d",
    },
  ];

  const feed = [
    "Mumbai transmission spike detected",
    "Pune recovery index improved",
    "AI outbreak engine updated",
    "Delhi entered moderate-risk state",
    "Containment success probability increased",
  ];

  return (
    <div className="app">

      <div className="background-grid"></div>

      <header className="topbar">
        <div>
          <h1>GLOBAL EPIDEMIC SURVEILLANCE SYSTEM</h1>
          <p>AI-powered outbreak intelligence & predictive analytics</p>
        </div>

        <div className="status-box">
          <span className="pulse"></span>
          LIVE MONITORING ACTIVE
        </div>
      </header>

      <div className="main-layout">

        <div className="left-panel">

          <motion.div
            className="glass-card giant-card"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h2>Threat Level</h2>

            <div className="threat-circle">
              HIGH
            </div>

            <p>
              AI systems indicate accelerated spread
              patterns across western monitoring zones.
            </p>
          </motion.div>

          <motion.div
            className="glass-card"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2>Live Activity Feed</h2>

            <div className="feed">
              {feed.map((item, index) => (
                <div className="feed-item" key={index}>
                  <span></span>
                  {item}
                </div>
              ))}
            </div>
          </motion.div>

        </div>

        <div className="center-panel">

          <motion.div
            className="glass-card graph-panel"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="graph-header">
              <h2>Outbreak Intelligence Overview</h2>

              <select>
                <option>Mumbai</option>
                <option>Pune</option>
                <option>Delhi</option>
                <option>Bangalore</option>
              </select>
            </div>

            <div className="fake-graph">
              <div className="graph-line"></div>
            </div>
          </motion.div>

          <div className="stats-grid">
            {stats.map((item, index) => (
              <motion.div
                className="glass-card stat-card"
                key={index}
                whileHover={{ scale: 1.04 }}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <h3>{item.title}</h3>

                <div
                  className="stat-number"
                  style={{ color: item.color }}
                >
                  <CountUp
                    end={item.value}
                    duration={2}
                    separator=","
                  />
                  {item.suffix}
                </div>
              </motion.div>
            ))}
          </div>

        </div>

        <div className="right-panel">

          <motion.div
            className="glass-card"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h2>AI Insights</h2>

            <div className="insight">
              <FaExclamationTriangle />
              Mumbai outbreak probability increased by 12%.
            </div>

            <div className="insight">
              <FaHeartbeat />
              Recovery stabilization detected in Pune.
            </div>

            <div className="insight">
              <FaShieldVirus />
              Containment effectiveness improving gradually.
            </div>

            <div className="insight">
              <FaBiohazard />
              Potential cluster expansion predicted within 7 days.
            </div>
          </motion.div>

          <motion.div
            className="glass-card radar-card"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2>Risk Radar</h2>

            <div className="radar">
              <div className="radar-ring"></div>
              <div className="radar-ring"></div>
              <div className="radar-ring"></div>
              <div className="radar-dot"></div>
            </div>
          </motion.div>

        </div>

      </div>
    </div>
  );
}

export default App;