# Heathrow regional illustration

`heathrow-west.json` includes OpenStreetMap ways and relations retrieved on 2 November
2026 from the public OSM map API. It contains Wraysbury Reservoir's shoreline,
Heathrow runway centrelines, mapped taxiways and terminal footprints. Each feature
retains its OSM ID, version, timestamp and original longitude/latitude pairs.
The source URLs and SHA-256 hashes of the downloaded XML responses are recorded.
Version 2 adds bounded connecting scenery and a separately attributed historical
FlightGear pavement layer. All original feature IDs and coordinates are retained.

Terminal 3 uses relation 18911624, outer way 151749316 and courtyard way
1372773206; their separate versions and timestamps are retained. `coordinates`
and `holes` preserve the original closed rings. `roofCoordinates` excludes their
duplicate closing vertices, and `roofTriangles` stores 320 precomputed triangles
with counter-clockwise winding in east/north coordinates. These were generated
offline using [mapbox-earcut 2.0.0](https://github.com/skogler/mapbox_earcut_python)
(ISC license); there is no application dependency. Shapely 2.0.7 independently
checked that their union exactly matches the polygon with its courtyard removed:
106,309.798 m² of roof, 200.591 m² of courtyard, no gaps or courtyard overlap.

Map data © OpenStreetMap contributors, available under the Open Database License
(ODbL) 1.0: https://www.openstreetmap.org/copyright and
https://opendatacommons.org/licenses/odbl/1-0/ . This extracted map database is
provided under that license; the separate FlightGear scenery retains GPL version 2.
The surrounding application retains its own license.
The reservoir way credits OS OpenData in the upstream OSM tags. See the individual
way's history at https://www.openstreetmap.org/way/147855503/history .

The driver projects coordinates about 51.4700° N, 0.4600° W using a local
 equirectangular projection, radius 6371.0088 km, x east and z north. One scene
unit equals one kilometre. Unity then scales to metres. The app shows the map
attribution, north direction and a 1 km scale in the regional overview.
This spherical approximation shortens the mapped east-west runway lengths by
about 0.3% versus a local WGS84 ellipsoid calculation (roughly 12 m over 4 km).
It does not support metre-accurate surveyed dimensions.

The [Environment Agency's Wraysbury geometry](https://environment.data.gov.uk/catchment-planning/WaterBody/GB30642417.geojson)
corroborates the reservoir outline: projected areas are 1.986216 km² (EA) and
1.986085 km² (OSM), with a largest vertex-to-other-boundary distance of 3.02 m.
The EA download labels its geometry as a catchment; this agreement does not
establish independent survey provenance or a current measured water level.
The [Department for Transport assessment, Table 2.2](https://assets.publishing.service.gov.uk/media/5b115e42e5274a18e5ea84cb/airports-nps-habitats-regulations-assessment-appendix-b.pdf)
places Wraysbury Reservoir 1.9 km west of Heathrow. In this extract the nearest
shore is about 2.05 km from the southern runway's physical western end; these
figures use different reference points.

The map also includes 34 complete, closed apron polygons from the same source
response. Their 651 precomputed roof triangles preserve 1,342,476.518 m² of mapped
pavement without overlaps or triangulation gaps. These surfaces sit beneath
buildings and taxiway ribbons. They add no guessed rectangular apron boundary.

The connected setting adds 264 mapped ground road centrelines, five mapped
pedestrian/parking surfaces, 41 nearby low-rise building footprints, 23 complete
water polygons and 15 mapped Terminal 2 passenger-bridge paths. Road/building
selection intersects the central terminal region, from -550 to 1300 m east and
-350 to 700 m north of the map origin; whole source ways are retained. Roads
tagged as tunnels, bridges, indoor, or on another layer/level are excluded from
this flat scene. Widths and absent heights have explicit authored basis fields.
The bridge plans are mapped; their 3 m width, 5 m walking floor and 3 m body height
are illustrative. Terminal 2A's 40 m height comes from its OSM tag; detailed roof
shape and other architectural dimensions remain authored. The
[T2B connection](https://www.balfourbeatty.com/what-we-do/projects/heathrow-airport-terminal-2b/)
and [T2–T3 passenger connection](https://www.heathrow.com/at-the-airport/lounges-hotels-spas/heathrow-hotels)
are underground, so no surface corridor is invented.

Three added water relations preserve 16 island holes. Incomplete multipolygons
1996194 and 2014584 are excluded because the response lacks some inner ways.
Every added polygon has precomputed triangulation with its holes removed; the
largest polygon-versus-triangle-union difference is below 0.000001 m². This is a
numerical geometry check, not a claim about survey accuracy or water level.

`roadTrafficRoutes` records one exact, shared-node, one-way loop of nine OSM ways,
1049.167 m long. Its centreline has no terminal intersection and lies at least
235.196 m from the existing runway/taxiway ribbons. Vehicle count, colour,
3 m/s speed and centreline lane placement are authored. The external scenario
clock controls movement; this ambient scenery creates no report evidence.

`referenceSites` keeps the January 2025 OSM outline of former Terminal 1 as an
outline only. [Heathrow's April 2026 update](https://www.heathrow.com/heathrow-blog/end-of-an-era-demolition-of-terminal-1)
describes phased demolition starting with Pier 4 while the remaining structure
supports Terminal 2 baggage. The old outline does not establish the present
standing extent and is not shown as an active, intact terminal.

The 46 additional pavement pieces come from official FlightGear scenery created
in October 2013. The limited crop around three T3 aprons excludes current mapped
grass, buildings, water, apron interiors and the former T1 footprint. Its exact
historical edges fill three mapped apron-to-taxiway gaps of about 29 m without
invented strips. All 278,232.591 m² retain source provenance; no claim of current
survey precision is made. Original BTG, hashes, GPL license, clipping inputs and
reproducible conversion are in `pavement/PROVENANCE.txt`. The independently
checked ECEF-to-WGS84 transform agrees to below 1.5e-14 degrees; source elevations
are flattened to the teaching scene. This dated pavement is a background layer
under current taxiway markings, not a replacement for current mapped geometry.

Terminal 3 combines its current mapped outline/courtyard with the detailed pier
from the free FlightGear TerraSync model and a custom entrance canopy based on
the independently mapped roof and fabricator's references. Original source,
licensing and limitations are in `terminal3/PROVENANCE.txt`; the runtime resource
is generated by `scripts/bake_terminal3.py`. It is a sourced architectural
illustration, not an exact current digital twin. The canopy's mapped plan,
11 m design height, pale ETFE roof and dark steel ribs are represented. Column
positions, glass bands and unmeasured remaining building heights are authored.
Reference photographs without reuse permission are not shipped as textures.

The depiction uses flat ground, generic aircraft and simplified pavement ribbons.
Unmeasured building heights, service details, flight trajectories,
water effects and event timing are authored. Displaced-threshold sections are
included as mapped; runway markings and lighting are not an AIP reproduction.
This is a geographic teaching illustration, not aerial imagery, a photorealistic
Heathrow reconstruction, a navigation chart or a performance/ditching simulation.

A real reservoir's presence does not establish a viable landing area. There is no
claim of a Heathrow reservoir accident, safe approach, obstacle clearance, water
level, survival outcome or locally achievable rescue time. Hudson Flight 1549 is
an incident-category precedent only; its location and outcome are not relocated.

For the full road-vehicle envelope check, use an isolated Python environment with Shapely 2.x and run `python scripts/verify_road_footprints.py --output work/road-footprint-check.json` from the repository root. It samples 4,000 poses against the renderer’s ribbons and source-node junctions, including the van’s wheels and lights. This verifies this authored loop, not arbitrary road traffic.
