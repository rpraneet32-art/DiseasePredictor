from flask import Flask, jsonify
from flask_cors import CORS

import requests

app = Flask(__name__)

CORS(app)


disease_data = [

    {
        "region":"Mumbai",
        "reportedCases":120
    },

    {
        "region":"Delhi",
        "reportedCases":90
    },

    {
        "region":"Bangalore",
        "reportedCases":70
    },

    {
        "region":"Chennai",
        "reportedCases":60
    }

]


def get_coordinates(city):

    url = (
        "https://nominatim.openstreetmap.org/search"
    )

    params = {
        "q": city,
        "format":"json",
        "limit":1
    }

    response = requests.get(
        url,
        params=params,
        headers={
            "User-Agent":"disease-dashboard"
        }
    )

    data = response.json()

    if data:

        return (
            float(data[0]["lat"]),
            float(data[0]["lon"])
        )

    return None


@app.route("/heatmap-data")

def heatmap_data():

    heatmap = []

    for item in disease_data:

        coords = get_coordinates(
            item["region"]
        )

        if coords:

            heatmap.append([

                coords[0],
                coords[1],
                item["reportedCases"]

            ])

    return jsonify(heatmap)


if __name__ == "__main__":

    app.run(debug=True)