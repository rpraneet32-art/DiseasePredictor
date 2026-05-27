import {
  MapContainer,
  TileLayer,
  useMap
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import L from "leaflet";

import "leaflet.heat";

import {
  useState,
  useEffect
} from "react";


function HeatLayer({ heatData }) {

  const map = useMap();

  useEffect(() => {

    if (!map || !heatData.length) return;

    const formattedData =
      heatData.map(point => [

        point[0],
        point[1],
        point[2] / 120

      ]);

    const heatLayer = L.heatLayer(

      formattedData,

      {
        radius:50,
        blur:35,
        maxZoom:10,

        gradient:{
          0.2:"blue",
          0.4:"lime",
          0.6:"yellow",
          0.8:"orange",
          1.0:"red"
        }
      }

    );

    heatLayer.addTo(map);

    return () => {

      map.removeLayer(heatLayer);

    };

  }, [map, heatData]);

  return null;
}


function Heatmap() {

  const [heatData, setHeatData]
  = useState([]);

  useEffect(() => {

    fetch(
      "http://127.0.0.1:5000/heatmap-data"
    )
      .then(res => res.json())
      .then(data => {

        setHeatData(data);

      })
      .catch(error => {

        console.error(error);

      });

  }, []);

  return (

    <div
      style={{
        height:"100vh",
        width:"100%",
      }}
    >

      <MapContainer
        center={[20.5937,78.9629]}
        zoom={5}
        style={{
          height:"100%",
          width:"100%"
        }}
      >

        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <HeatLayer heatData={heatData} />

      </MapContainer>

    </div>

  );

}

export default Heatmap;