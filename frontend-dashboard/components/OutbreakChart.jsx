import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js"

import { Line } from "react-chartjs-2"

import outbreakData from "../data/dummyData"

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
)

function OutbreakChart({ selectedDisease, selectedRegion }) {

  const currentData =
  outbreakData[selectedDisease][selectedRegion].weeklyData

  const data = {
    labels: currentData.map((item) => item.day),

    datasets: [
      {
        label: "Predicted Cases",
        data: currentData.map((item) => item.cases),
        borderColor: "#f87171",
        backgroundColor: "#f87171",
        tension: 0.4,
      },
    ],
  }

  const options = {
    responsive: true,

    plugins: {
      legend: {
        labels: {
          color: "white",
        },
      },
    },

    scales: {
      x: {
        ticks: {
          color: "white",
        },
      },

      y: {
        ticks: {
          color: "white",
        },
      },
    },
  }

  return (
    <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl">

      <div className="flex items-center justify-between mb-6">

        <h2 className="text-2xl font-semibold">
          Weekly Outbreak Trend
        </h2>

        <button className="bg-white/10 hover:bg-white/20 transition px-4 py-2 rounded-xl text-sm">
          Last 7 Days
        </button>

      </div>

      <Line data={data} options={options} />

    </div>
  )
}

export default OutbreakChart