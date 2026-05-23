const outbreakData = {
  Flu: {
    Maharashtra: {
      probability: 82,
      growth: 12,
      predictedCases: 245,
      risk: "High",
      temperature: 31,
      humidity: 76,

      weeklyData: [
        { day: "Mon", cases: 120 },
        { day: "Tue", cases: 190 },
        { day: "Wed", cases: 300 },
        { day: "Thu", cases: 250 },
        { day: "Fri", cases: 400 },
        { day: "Sat", cases: 520 },
        { day: "Sun", cases: 460 },
      ],
    },

    Delhi: {
      probability: 68,
      predictedCases: 180,
      risk: "Medium",
      temperature: 34,
      humidity: 60,

      weeklyData: [
        { day: "Mon", cases: 90 },
        { day: "Tue", cases: 130 },
        { day: "Wed", cases: 210 },
        { day: "Thu", cases: 260 },
        { day: "Fri", cases: 340 },
        { day: "Sat", cases: 390 },
        { day: "Sun", cases: 430 },
      ],
    },
  },

  Dengue: {
    Maharashtra: {
      probability: 91,
      predictedCases: 390,
      risk: "High",
      temperature: 29,
      humidity: 88,

      weeklyData: [
        { day: "Mon", cases: 80 },
        { day: "Tue", cases: 140 },
        { day: "Wed", cases: 220 },
        { day: "Thu", cases: 310 },
        { day: "Fri", cases: 450 },
        { day: "Sat", cases: 490 },
        { day: "Sun", cases: 530 },
      ],
    },

    Delhi: {
      probability: 58,
      predictedCases: 140,
      risk: "Low",
      temperature: 36,
      humidity: 52,

      weeklyData: [
        { day: "Mon", cases: 60 },
        { day: "Tue", cases: 100 },
        { day: "Wed", cases: 170 },
        { day: "Thu", cases: 240 },
        { day: "Fri", cases: 330 },
        { day: "Sat", cases: 410 },
        { day: "Sun", cases: 470 },
      ],
    },
  },
}

export default outbreakData