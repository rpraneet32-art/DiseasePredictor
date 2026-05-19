import { useState } from "react"
import OutbreakChart from "./components/OutbreakChart"
import outbreakData from "./data/dummyData"

function App() {

  const diseases = Object.keys(outbreakData)

  const [selectedDisease, setSelectedDisease] =
    useState(diseases[0])

  const [selectedRegion, setSelectedRegion] =
    useState(
      Object.keys(outbreakData[diseases[0]])[0]
    )

  const currentStats =
    outbreakData[selectedDisease][selectedRegion]

  const weeklyData = currentStats.weeklyData

  const latestCases =
    weeklyData[weeklyData.length - 1].cases

  const previousCases =
    weeklyData[weeklyData.length - 2].cases

  const growth =
    ((latestCases - previousCases) / previousCases) * 100

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 text-white px-8 py-6">

      {/* Navbar */}
      <div className="flex items-center justify-between mb-10">

        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            Disease Outbreak Predictor
          </h1>

          <p className="text-gray-400 mt-2 text-sm">
            Real-time outbreak monitoring and forecasting dashboard
          </p>
        </div>

        {/* Dynamic Risk Badge */}
        <div
          className={`
            px-4 py-2 rounded-full border
            ${
              currentStats.risk === "High"
                ? "bg-red-500/20 border-red-500/30"
                : currentStats.risk === "Medium"
                ? "bg-yellow-500/20 border-yellow-500/30"
                : "bg-green-500/20 border-green-500/30"
            }
          `}
        >
          <span
            className={`
              font-semibold
              ${
                currentStats.risk === "High"
                  ? "text-red-400"
                  : currentStats.risk === "Medium"
                  ? "text-yellow-400"
                  : "text-green-400"
              }
            `}
          >
            {currentStats.risk} Risk Zone
          </span>
        </div>

      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-8">

        {/* Disease Dropdown */}
        <select
          value={selectedDisease}
          onChange={(e) => {

            const disease = e.target.value

            setSelectedDisease(disease)

            const firstRegion =
              Object.keys(
                outbreakData[disease]
              )[0]

            setSelectedRegion(firstRegion)
          }}
          className="bg-gray-900 text-white border border-white/10 px-4 py-3 rounded-2xl outline-none"
        >
          {Object.keys(outbreakData).map(
            (disease) => (
              <option
                key={disease}
                className="bg-gray-900"
                value={disease}
              >
                {disease}
              </option>
            )
          )}
        </select>

        {/* Region Dropdown */}
        <select
          value={selectedRegion}
          onChange={(e) =>
            setSelectedRegion(e.target.value)
          }
          className="bg-gray-900 text-white border border-white/10 px-4 py-3 rounded-2xl outline-none"
        >
          {Object.keys(
            outbreakData[selectedDisease]
          ).map((region) => (
            <option
              key={region}
              className="bg-gray-900"
              value={region}
            >
              {region}
            </option>
          ))}
        </select>

      </div>

      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

        {/* Probability Card */}
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl">

          <p className="text-gray-400 text-sm">
            Outbreak Probability
          </p>

          <h2 className="text-5xl font-bold mt-4">
            {currentStats.probability}%
          </h2>

          <p
            className={`mt-3 text-sm ${
              growth >= 0
                ? "text-green-400"
                : "text-red-400"
            }`}
          >
            {growth >= 0 ? "↑" : "↓"}{" "}
            {Math.abs(growth).toFixed(1)}%
            {" "}
            from last week
          </p>

        </div>

        {/* Cases Card */}
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl">

          <p className="text-gray-400 text-sm">
            Predicted Cases
          </p>

          <h2 className="text-5xl font-bold mt-4">
            {currentStats.predictedCases}
          </h2>

          <p className="text-yellow-400 mt-3 text-sm">
            {selectedRegion}
          </p>

        </div>

        {/* Disease Card */}
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl">

          <p className="text-gray-400 text-sm">
            Active Disease
          </p>

          <h2 className="text-5xl font-bold mt-4">
            {selectedDisease}
          </h2>

          <p className="text-red-400 mt-3 text-sm">
            {currentStats.risk} Risk Detected
          </p>

        </div>

      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Chart */}
        <div className="lg:col-span-2">

          <OutbreakChart
            selectedDisease={selectedDisease}
            selectedRegion={selectedRegion}
          />

        </div>

        {/* Region Details */}
        <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl">

          <h2 className="text-2xl font-semibold mb-6">
            Region Details
          </h2>

          <div className="space-y-5">

            <div className="bg-white/5 p-4 rounded-2xl">

              <p className="text-gray-400 text-sm">
                Region
              </p>

              <h3 className="text-xl font-semibold mt-1">
                {selectedRegion}
              </h3>

            </div>

            <div className="bg-white/5 p-4 rounded-2xl">

              <p className="text-gray-400 text-sm">
                Temperature
              </p>

              <h3 className="text-xl font-semibold mt-1">
                {currentStats.temperature}°C
              </h3>

            </div>

            <div className="bg-white/5 p-4 rounded-2xl">

              <p className="text-gray-400 text-sm">
                Humidity
              </p>

              <h3 className="text-xl font-semibold mt-1">
                {currentStats.humidity}%
              </h3>

            </div>

          </div>

        </div>

      </div>

    </div>
  )
}

export default App