# Bounded wide-airport scenery audit

3 November 2026. Independent Astra visual/reference pass for issue #59. No renderer, source data, video, script, or live-service changes were made. The original user-reported camera/view remains unidentified. The previous 19-frame presentation review was not repeated.

## Finding

No incorrect island enclosing Heathrow is established by this pass. The actual saved Region overview shows continuous green terrain around the airport, a separate Wraysbury Reservoir to its west/southwest, and a group of irregular water bodies with land holes farther west. Those irregular islands belong to mapped lake polygons, not the airport boundary. Removing those holes or filling that lake group would contradict the saved placement source.

This is a matched geographic-feature check of the saved native Region view against its mapped source: reservoir, western lake group, two east–west runways and their relative positions. It is not an exact perspective-matched aerial survey, not the unknown original reported view, and not a new capture of the currently running build.

## Images directly inspected

- `outputs/label-fix-landscape-region.png`: native landscape Region view, scenario 01:48, runway-occupied go-around. Both runways and the western lakes are visible on connected terrain. The reservoir is elongated northeast–southwest; separate irregular lake polygons lie to its west and southwest; Heron Lake is farther south. No water surrounds the airport. This previously saved capture has four separated flight labels and the Terminals button. Its prior provenance is `outputs/label-fix-review.json`; it is newer geometry than the water-landing movie below.
- `work/wide-scenery-frames/water-landing-native-0003.png`: newly extracted at exactly requested 3.000 s from `outputs/airfieldlens-water_landing-native.mp4`, scenario 00:01. Wide Region composition shows the airport and one separate Wraysbury Reservoir on continuous green terrain. This older capture lacks the added surrounding lake group. The left black pill is device/UI masking, not terrain.
- `work/wide-scenery-frames/walkthrough-1049.608.png`: newly extracted from `outputs/AirfieldLens-walkthrough.mp4` at requested 1049.608 s (17:29.608). Directly confirms that the assembled long walkthrough contains this older wide water-landing view, with the same continuous land and separate reservoir. Exact requested extraction used AVAssetImageGenerator with zero time tolerances. The extractor does not report returned presentation timestamp, so do not claim a separately verified actual PTS.
- `work/terminal3-reference/aerial-2010.jpg`: historical oblique airport photograph. It establishes connected apron/runway land and separated distant water, but does not cover the western lake group at a suitable angle/resolution for boundary comparison. It is not camera-matched to the Region view and cannot establish current geometry. Source page is recorded in `work/terminal3-reference/reference-image-urls.json`.
- `outputs/apronlens-custom-heathrow-overview.png`: inspected only to determine usefulness; this is a close apron/terminal view despite its filename and adds no evidence about the regional perimeter.

## Fresh source verification

Read current `R/data/geography/heathrow-west.json` and independently reconstructed all 24 water polygons from the two saved raw OSM XML files in `work/runway-extension`. Both XML SHA256 values match the geography source declarations. All 24 current water polygons have zero symmetric-difference area against their raw XML polygon sources. Where stored roof triangulation exists, its union has zero symmetric-difference area against the water polygon, including holes. This was run in memory without overwriting the earlier audit.

The often-cited 23 count applies to connected-setting additions; the full geography has 24 water features including original Wraysbury Reservoir (`osm-way-147855503`). Relations 1995967, 1996199 and 1996200 retain 3, 12 and 1 holes respectively. Wraysbury projected bounds are x −5308.6…−3889.8 m, north −2097.4…109.3 m. The three holed water relations are farther west, x approximately −6561…−5553 m. These match the reservoir-versus-western-lakes placement in the saved Region screenshot.

Using the current runway centreline geometries, neither main runway intersects mapped water. Their nearest mapped water distances are 778.329 m (09R/27L) and 459.205 m (09L/27R). These are centreline-to-polygon distances, not certified runway-edge clearance measurements. The current renderer builds a 32 × 24 km green regional terrain box (`TrainingGeography.cs`, line 71), not a water background with an airport island cutout. This code reading supports but does not replace a current native render.

Current geography SHA256: `5081a359bfcb2b09c189e5714be160c3e8ccaab513b41800a416acb7369c689d`.

## Remedy and video impact

No geometry edit is justified by the verified evidence. A cosmetic island-removal patch would be an invented remedy. Keep #59 open until its actual reported view is identified/reproduced, or document a product/design concern separately if the intent is more surrounding land detail rather than incorrect mapped geometry.

No correction to the eight-minute presentation or speaking cues is supported by this new wide-view evidence. The long walkthrough explicitly contains an older, simpler regional view; this is a version/level-of-detail difference, not the reported false-island defect. Do not describe that older shot as showing every current mapped waterbody or the latest connected scenery. No broad re-recording recommendation is warranted, and no full continuous video clearance is claimed.

Smallest next check: after the coordinator's model work is finished, capture the current native app at Region view and compare it to `label-fix-landscape-region.png`. If the user identifies another view, preserve its scenario, camera, zoom, orientation and source time before changing geometry.

## Image hashes

- `outputs/label-fix-landscape-region.png` — `f229d01b74567fe936b878adc3ff84071d1ccd0c777ce2d55ecbd0f5c177e62b`
- `work/wide-scenery-frames/water-landing-native-0003.png` — `0295e0733a229b2435098564c7ab9a8eff4a69aa2bc2b8688386f8b2321a928e`
- `work/wide-scenery-frames/walkthrough-1049.608.png` — `8c34123c62cbfbac376fe3f636f34746e8d3ebfa05c8aa829da5b9e9db3e2ef6`

## Current native availability check

The requested smallest follow-up ran `xcrun simctl list devices booted`. No devices were booted (empty iOS 27.0 and 27.1 sections). Therefore no current app state or Region camera was available without starting a simulator. No simulator, app, model service or rebuild was started, and no new current-native validation is claimed. Fresh machine-readable geometry verification is preserved in `work/wide-scenery-source-audit.json`.
