# Aircraft exteriors

AirfieldLens uses the A320, A380, B737 and B787 family models by AMV Lab (amvlab), 2026, under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

Original source: https://github.com/amvlab/aircraft-models at commit `91d835e8e851b2317fe79af291c9fed6153fd525`. Original GLBs, README and license are preserved here. `conversion.json` records input hashes and transformations; `scripts/bake_aircraft.py` reproduces the runtime assets without external packages.

Changes: source transforms baked; nose reoriented to +Z; overall length, span and height normalized independently to the stated aircraft reference; textures extracted; original retractable landing gear added. These are family exterior assets normalized to nominal reference dimensions, not exact variant CAD or aircraft-performance models. Minimum exterior clearance and gear strut heights are authored approximations. The models do not establish aircraft-specific failure tendencies.

Reference envelope and gear stations: Airbus A320 airport planning July 2026 (A320-200 Sharklets); Boeing 737NG airport planning Rev C October 2025 (737-800 winglets); Boeing 787 airport planning Rev Q October 2025 (787-8); Airbus A380 airport planning December 2025 (A380-800). A380 reference height is 24.12 metres; real parked heights depend on load.

- https://mediaassets.airbus.com/pm_38_916_916266-iujedqawwy.pdf?fileName=aca32001-jul-2026-2.pdf
- https://www.boeing.com/content/dam/boeing/v2/airports/acaps/737NG_REV_C.pdf
- https://www.boeing.com/content/dam/boeing/v2/airports/acaps/787_ACAP_Rev_Q.pdf
- https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2025-12/AC_A380_20251201.pdf
