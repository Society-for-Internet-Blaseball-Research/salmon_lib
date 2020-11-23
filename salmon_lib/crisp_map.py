import json
import matplotlib.pyplot as plt
import sys
import salmon_lib.resources
import importlib.resources
from math import floor

"""
Python script for generating a valid `map.dat` file for use in CRiSP Harvest v3.0.6.

Usage:
  `python -m salmon_lib.crisp_map > map.dat`

If you want to display the map in the CRiSP Harvest Simulator Simulator:
  `python -m salmon_lib.crisp_map display`


Map credits:

Map data was derived from SVG files found on Wikimedia under a Creative Commons
Attribution-Share Alike license. SVG path data was extracted and converted into
pixel coordinates.

  North America:
    https://commons.wikimedia.org/wiki/File:North_America_map_with_states_and_provinces.svg
  Hawai'i:
    https://commons.wikimedia.org/wiki/File:Hawaii_presidential_election_results_2012.svg
  Japan:
    https://commons.wikimedia.org/wiki/File:Shinano_river_Route.svg
"""

# Once the maps are scaled down, this allows a common offset in case we want
# to slide North America (and all its fisheries) over or something.
OFFSETS_BY_MAP = {
    "north_america": (0.05, -0.05),
    "hawaii": (-0.16, 0.22),
    "japan": (-0.081, 0.47),
}

# Different maps need different projections from the pixel coordinates
# found in their source SVG files into xy coord space.
# In xy space, the viewport is bounded by x := [0, 1], y := [0, 1]


def na_pixels_to_xy(pixel_coord, pathtype):
    x, y = pixel_coord
    # First, normalize x & y as fractions of position in the image, and center
    if pathtype == "coastline" or pathtype == "water":
        # I don't know why but it is what it is
        y += 300.63782
    # Size of the original SVG
    x /= 1300
    y /= 1353
    # eyeballed these, so the map is less squished and we get Mexico in there
    y = 1.62 * y - 0.45
    dx, dy = OFFSETS_BY_MAP["north_america"]
    x += dx
    y += dy
    return (x, y)


def hawaii_pixels_to_xy(pixel_coord):
    x, y = pixel_coord
    x /= 274 * 5
    y /= 160 * 5
    dx, dy = OFFSETS_BY_MAP["hawaii"]
    x += dx
    y += dy
    return (x, y)


def japan_pixels_to_xy(pixel_coord):
    x, y = pixel_coord
    x -= -3948.05
    y -= -315.0128
    x /= 1500 * 40
    y /= 1500 * 30
    dx, dy = OFFSETS_BY_MAP["japan"]
    x += dx
    y += dy
    return (x, y)


# "Crisp space" denotes the boundaries of the default viewport of CRiSP's map.
# lat, lon coordinates from within the program for that. Note this forms a
# trapezoid: CRiSP does some built-in mercator projection, which we have to
# counteract to make the maps lie flat...ish.
CRISP_CORNERS = {
    "NW": {"lat": 60, "lon": 153},
    "NE": {"lat": 60, "lon": 92.5},
    "SE": {"lat": 42.5, "lon": 102},
    "SW": {"lat": 42.5, "lon": 142},
}


def xy_to_crisp(xy_coord):
    """
    Project the rectangular xy space into the trapezoidal crisp space
    """
    x, y = xy_coord

    # Latitude doesn't skew, thankfully
    top = CRISP_CORNERS["NW"]["lat"]
    bottom = CRISP_CORNERS["SE"]["lat"]
    lat = top + y * (bottom - top)

    """
  lon = a*x + b*y + c*x*y + lon_0
  lon_NW = a*0 + b*0 + c*0*0 + lon_0 = lon_NW
  lon_NE = a*1 + b*0 + c*0*0 lon_0 = a + lon_NW
  a = lon_NE - lon_NW
  lon_SW = a*0 + b*1 + c*0*0 + lon_0 = b + lon_NW
  b = lon_SW - lon_NW
  lon_SE = a + b + c + lon_NW
  c = lon_SE - a - b - lon_NW
  """
    lon_NW = CRISP_CORNERS["NW"]["lon"]
    lon_NE = CRISP_CORNERS["NE"]["lon"]
    lon_SW = CRISP_CORNERS["SW"]["lon"]
    lon_SE = CRISP_CORNERS["SE"]["lon"]
    a = lon_NE - lon_NW
    b = lon_SW - lon_NW
    c = lon_SE - a - b - lon_NW
    lon = lon_NW + (a * x) + (b * y) + (c * x * y)
    return (lat, lon)


def na_latlong_to_na_pixels(na_latlong_coord):
    """
    Blaseball teams had real latlong coordinates, but North America is
    only available in SVG pixel space, xy space, or crisp space.
    This method projects real latlong coordinates into xy space,
    so we can plot them on the continent.

    To accomplish this, we mark the real latlong and xy space coordinates for
    four tiny islands near the four corners of North America:

      (lat, lon) => (pixel_x, pixel_y)
      Staten Island: (40.5831432, -74.1660104) => (1023.513, 438.125)
      Key West: (24.5568229, -81.7855996) => (972.400, 779.157)
      Socorro Island: (18.7902148, -110.9893702) => (429.9429, 911.7857)
      Marina Island: (50.0725441, -125.0385159) => (329.5364, 260.591)

    What then follows is math to project other latlong coordinates into xy space
    using those four points as guides.

    (Not currently in use, but important for documentation purposes.)
    """
    real_lat, real_lon = na_latlong_coord
    # pixel_y = m*lat + pixel_y_0
    # Computed in Excel using the above data
    pixel_y = -20.864 * real_lat + 1296.4
    """
  pixel_x = (a * lat) + (b * lon) + (c * lat * lon) + d

  1023.513 = (a * 40.5831432) + (b * -74.1660104) + (c * 40.5831432 * -74.1660104) + d
  972.400 = (a * 24.5568229) + (b * -81.7855996) + (c * 24.5568229 * -81.7855996) + d
  429.9429 = (a * 18.7902148) + (b * -110.9893702) + (c * 18.7902148 * -110.9893702) + d
  329.5364 = (a * 50.0725441) + (b * -125.0385159) + (c * 50.0725441 * -125.0385159) + d
  Solved w/ WolframAlpha:
  a = -21.2702 and b = 23.3396 and c = -0.213838 and d = 2974.1
  """
    a = -21.2702
    b = 23.3396
    c = -0.213838
    d = 2974.1
    pixel_x = (a * real_lat) + (b * real_lon) + (c * real_lat * real_lon) + d
    return (pixel_x, pixel_y)


ALL_TEAMS = [
    {
        "name": "Miami Dale",
        "map": "north_america",
        "real_latlong_coord": (25.7774348, -80.2225358),
        "xy": (0.76568, 0.80298),
    },
    {
        "name": "Mexico City Wild Wings",
        "map": "north_america",
        "real_latlong_coord": (19.3027606, -99.153255),
        "xy": (0.5037, 1.000),
    },
    {
        "name": "Unlimited Tacos",
        "map": "north_america",
        "real_latlong_coord": (34.079658, -118.411653),
        "xy": (0.26118, 0.6179),
    },
    {
        "name": "New York Millennials",
        "map": "north_america",
        "real_latlong_coord": (40.564521, -74.2869045),
        "xy": (0.78756, 0.4333),
    },
    {
        "name": "Boston Flowers",
        "map": "north_america",
        "real_latlong_coord": (42.3661864, -71.0644182),
        "xy": (0.81165, 0.3767),
    },
    {
        "name": "Kansas City Breath Mints",
        "map": "north_america",
        "real_latlong_coord": (39.051647, -94.480582),
        "xy": (0.5572, 0.5394),
    },
    {
        "name": "Philly Pies",
        "map": "north_america",
        "real_latlong_coord": (39.9060572, -75.1686839),
        "xy": (0.77837, 0.4541),
    },
    {
        "name": "Houston Spies",
        "map": "north_america",
        "real_latlong_coord": (29.7572694, -95.357703),
        "xy": (0.5561, 0.7544),
    },
    {
        "name": "Dallas Steaks",
        "map": "north_america",
        "real_latlong_coord": (32.8203525, -97.0117397),
        "xy": (0.5204, 0.6770),
    },
    {
        "name": "Yellowstone Magic",
        "map": "north_america",
        "real_latlong_coord": (44.4604788, -110.8303264),
        "xy": (0.3764, 0.4050),
    },
    {
        "name": "Chicago Firefighters",
        "map": "north_america",
        "real_latlong_coord": (41.8297859, -87.635965),
        "xy": (0.63255, 0.4610),
    },
    {
        "name": "Hellmouth Sunbeams",
        "map": "north_america",
        "real_latlong_coord": (38.5743966, -109.5689282),
        "xy": (0.3783, 0.5486),
    },
    {
        "name": "Breckenridge Jazz Hands",
        "map": "north_america",
        "real_latlong_coord": (39.501221, -106.1132514),
        "xy": (0.42226, 0.5260),
    },
    {
        "name": "Seattle Garages",
        "map": "north_america",
        "real_latlong_coord": (47.5914026, -122.3346972),
        "xy": (0.26699, 0.2905),
    },
    {
        "name": "Baltimore Crabs",
        "map": "north_america",
        "real_latlong_coord": (39.283923, -76.621552),
        "xy": (0.765215, 0.476931),
    },
    {
        "name": "San Francisco Lovers",
        "map": "north_america",
        "real_latlong_coord": (37.7784964, -122.3896875),
        "xy": (0.226388, 0.51762),
    },
    {
        "name": "Charleston Shoe Thieves",
        "map": "north_america",
        "real_latlong_coord": (32.790353, -79.961334),
        "xy": (0.748283, 0.643998),
    },
    {
        "name": "Canada Moist Talkers",
        "map": "north_america",
        "real_latlong_coord": (44.647272, -63.580331),
        "xy": (0.870434, 0.272425),
    },
    {
        "name": "Hades Tigers",
        "map": "north_america",
        "real_latlong_coord": (42.4344751, -83.9857153),
        "xy": (0.669666, 0.434666),
    },
    {
        "name": "Hawai'i Fridays",
        "map": "hawaii",
        "real_latlong_coord": (21.3279758, -157.9391615),
        "xy": (0.368397, 0.67793),
    },
    {
        "name": "Tokyo Lift",
        "map": "japan",
        "real_latlong_coord": (35.6681625, 139.600781),
        "xy": (0.229471, 0.125595),
    },
]


def add_team_fishery(team):
    if "hidden" in team and team["hidden"]:
        return
    name = team["name"]
    x, y = team["xy"]
    dx, dy = OFFSETS_BY_MAP[team["map"]]
    x += dx
    y += dy
    if should_display():
        plt.scatter([x], [y], color="red")
        plt.text(
            x,
            y,
            "  " + name,
            color="red",
            fontsize="xx-small",
            va="baseline",
        )
        return
    render_fishery(name, (x, y))


def add_north_america(north_america_data):
    for path in north_america_data:
        pathtype = path["type"]
        xy_coord_list = [
            na_pixels_to_xy(pixel_coord, pathtype) for pixel_coord in path["path"]
        ]
        render_path(pathtype, xy_coord_list)


def add_hawaii(hawaii_data):
    for path in hawaii_data:
        pathtype = path["type"]
        xy_coord_list = [
            hawaii_pixels_to_xy(pixel_coord) for pixel_coord in path["path"]
        ]
        render_path(pathtype, xy_coord_list)
    # draw red inset map boundary, for style points
    render_boundary_path(
        "hawaii",
        [
            (0.02, 0.72),
            (0.245, 0.72),
            (0.23, 0.96),
            (-0.003, 0.96),
            (0.02, 0.72),
        ],
    )


def add_japan(japan_data):
    for path in japan_data:
        pathtype = path["type"]
        xy_coord_list = [
            japan_pixels_to_xy(pixel_coord) for pixel_coord in path["path"]
        ]
        render_path(pathtype, xy_coord_list)
    # draw red inset map boundary, for style points
    render_boundary_path(
        "japan",
        [
            (0.035, 0.40),
            (0.253, 0.40),
            (0.245, 0.72),
            (0.02, 0.72),
            (0.035, 0.40),
        ],
    )


def should_display():
    if len(sys.argv) == 1:
        return False
    return sys.argv[1] in ["d", "display"]


# Begin methods which either print valid map.dat syntax,
# or plot data onto a matplotlib graph.
def render_path(pathtype, xy_coord_list):
    if should_display():
        xs, ys = zip(*xy_coord_list)
        colors = {
            "coastline": "black",
            "river": "blue",
            "water": "grey",
            "island": "grey",
            "ice": "grey",
        }
        plt.plot(xs, ys, color=colors[pathtype])
        return
    start_blocks = {
        "coastline": "coastline",
        "river": "river River",
        "water": "island waterbody",
        "island": "island innerisland",
        "ice": "island icebody",
    }
    end_blocks = {
        "coastline": "end (coastline)",
        "river": "end (river River)",
        "water": "end (waterbody)",
        "island": "end (innerisland)",
        "ice": "end (icebody)",
    }
    print("")
    print(start_blocks[pathtype])
    for xy_coord in xy_coord_list:
        lat, lon = xy_to_crisp(xy_coord)
        # print('-%3f,%3f' % (lon,lat))
        print("latlon %s N %s W" % (latlonstr(lat), latlonstr(lon)))
    print(end_blocks[pathtype])


def render_boundary_path(prefix, xy_coord_list):
    if should_display():
        xs, ys = zip(*xy_coord_list)
        plt.plot(xs, ys, color="red")
        return
    for i in range(len(xy_coord_list) - 1):
        name = "%s_%d" % (prefix, i)
        print("")
        print("boundary %s" % name)
        lat, lon = xy_to_crisp(xy_coord_list[i])
        print("latlon %s N %s W" % (latlonstr(lat), latlonstr(lon)))
        lat, lon = xy_to_crisp(xy_coord_list[i + 1])
        print("latlon %s N %s W" % (latlonstr(lat), latlonstr(lon)))
        print("end (%s)" % name)


def render_fishery(name, xy_coord):
    if should_display():
        x, y = xy_coord
        plt.scatter([x], [y], color="red")
        plt.text(
            x,
            y,
            "  " + name,
            color="red",
            fontsize="xx-small",
            va="baseline",
        )
        return
    lat, lon = xy_to_crisp(xy_coord)
    print("")
    print("fishery %s" % name)
    print("icon_location %s N %s W" % (latlonstr(lat), latlonstr(lon)))
    print("end (%s)" % name)


def latlonstr(num):
    degrees = floor(num)
    num -= degrees
    num *= 60
    minutes = floor(num)
    num -= minutes
    num *= 60
    seconds = round(num)
    return "%02d %02d %02d" % (degrees, minutes, seconds)


if __name__ == "__main__":
    with importlib.resources.open_text(
        salmon_lib.resources, "crisp_map_data.json"
    ) as f:
        crisp_map_data = json.load(f)
    add_north_america(crisp_map_data["north_america"])
    add_hawaii(crisp_map_data["hawaii"])
    add_japan(crisp_map_data["japan"])
    for team in ALL_TEAMS:
        add_team_fishery(team)

    if should_display():
        plt.gcf().canvas.set_window_title("CRiSP Harvest Simulator Simulator")
        plt.axis([0, 1, 0, 1])
        plt.gca().invert_yaxis()
        plt.show()
