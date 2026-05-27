import requests

def get_coordinates(city):

    url = (
        "https://nominatim.openstreetmap.org/search"
    )

    params = {
        "q": city,
        "format": "json",
        "limit": 1
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

        return {
            "lat": float(data[0]["lat"]),
            "lng": float(data[0]["lon"])
        }

    return None


print(
    get_coordinates("Mumbai")
)