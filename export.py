import io
import folium
import tempfile

from folium.features import DivIcon
from PIL import Image
from shapely.geometry import Point, mapping, shape

with tempfile.TemporaryDirectory(dir="/tmp") as tempdir:
    map_path = "{}/map.html".format(tempdir)
    image_path = "{}/image.png".format(tempdir)
  
    # Create map
    map = folium.Map([-23.682567,-46.666548], zoom_start=14, tiles="cartodbpositron")
  
    # Marker my location
    folium.Marker([-23.682567,-46.666548] ).add_to(map)

    focos = [
      [ -46.636548, -23.682567 ],
      [ -46.666548, -23.712567 ],
      [ -46.696548, -23.682567 ],
      [ -46.666548, -23.652567 ],
    ]

    for f in focos:
        folium.Marker(
            location=[f[1], f[0]],
            icon=folium.Icon(color="red",icon="fire"),
        ).add_to(map)

        folium.map.Marker([f[1], f[0]],
            icon=DivIcon(
                icon_size=(150,36),
                icon_anchor=(0,0),
                html='<div style="font-size: 12pt">%s</div>' % '2021-07-20T16:24:00+00:00',
            )
        ).add_to(map)

    # Buffer Location area
    patch = Point(-46.666548, -23.682567).buffer(0.02)
    geojson = mapping(patch)
    folium.GeoJson(geojson).add_to(map)
   
    # Save map
    map.save("map_path.html")

    # Convert map to PNG
    img_data = map._to_png(5)
    img = Image.open(io.BytesIO(img_data))
    img.save("image.png")