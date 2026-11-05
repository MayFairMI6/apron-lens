# Heathrow procedure references

The fleet demonstration uses independently authored movement informed by a small set of published Heathrow runway and approach facts. It does not reproduce a complete departure, arrival or missed-approach procedure. Speeds, acceleration, rotation, flare, incident timing and aircraft-system behaviour remain authored illustrations; they are not certified performance data or reconstructed flights.

The [NATS AIP publication page](https://nats-uk.ead-it.com/cms-nats/opencms/en/Publications/AIP/) identified AIRAC 11/2026, effective **29 October 2026**, as the applicable published cycle when checked on 3 November 2026. The next listed cycle was 26 November. This is a pinned reference cycle, not a claim that the application follows live operational changes. No operational NOTAM review was performed.

## Runway and approach facts

[NATS EGLL AD 2.12–2.13](https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-10-29-AIRAC/html/eAIP/EG-AD-2.EGLL-en-GB.html) gives Runway 09R threshold coordinates as 51°27′53.25″N, 000°28′56.33″W (51.464791667, −0.482313889), true bearing 089.68°, and threshold elevation 75.3 feet above mean sea level. The physical runway is 3,658 by 50 metres; the 09R landing threshold is displaced 308 metres, leaving a landing distance available of 3,350 metres.

The mapped scene centreline is approximately 3.34 kilometres long. Its western endpoint must be compared with the published landing threshold before using the displacement; adding 308 metres to a line already starting at the landing threshold would apply the displacement twice. Scene ground is a flattened local surface, not a surveyed elevation model. Threshold elevation is an altitude datum conversion, not a command to raise the aircraft 75.3 feet above that surface.

The [ILS/DME I-BB Runway 09R chart, AD 2-EGLL-8-4](https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-10-29-AIRAC/graphics/505230.pdf), has aeronautical information date 20 April 2026 and change identifier 7/26 within that cycle. It specifies a 3.0° glide path and 50-foot reference datum height. Its track is 088° magnetic, with a chart variation of 1.2° east at epoch 2027. Chart tracks are rounded; use published true runway alignment for the geographic scene rather than treating magnetic degrees as true coordinates.

The 50-foot datum belongs to the approach reference, not automatically to the model's main-wheel root. The visualization must distinguish that reference from gear contact, its authored flare and touchdown location. A family exterior mesh does not establish the aircraft's actual navigation antenna position. Any visual approximation must be named as such in implementation provenance.

The same chart describes an initial straight-ahead missed approach to 3,000 feet above mean sea level, followed by further direction. Relative to the 75.3-foot threshold, that altitude is 2,924.7 feet (891.44856 metres) above the flattened threshold datum. The separate right turn at LON DME 10 toward EPM is a **radio-failure branch**; it must not be applied to the ordinary runway-occupied go-around. The demonstration does not implement that branch, subsequent ATC vectoring or a complete re-approach.

## Departure scope

The [BPK departure chart, AD 2-EGLL-6-3](https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-10-29-AIRAC/graphics/475388.pdf) was inspected. BPK 6J for 09R contains DME-defined turns, magnetic tracks and crossing-altitude constraints, and is marked RNAV substitution only. A straight departure in the demonstration is therefore not labelled a reproduction of BPK 6J or another published SID. Full SID adoption remains unverified and outside this bounded change.

An earlier search lead for temporary TANGO supplement 054/2026 returned 404 during this review and was absent from the current supplement listing. It was not used to modify the pinned procedure. Supplement listings can retain date-limited entries; their presence alone does not establish current applicability.

## Source use and verification limits

[NATS AIS terms](https://nats-uk.ead-it.com/cms-nats/opencms/en/agb/) incorporate the [general website terms](https://www.nats.aero/home/terms-and-conditions/). Those terms reserve rights and limit derivative and commercial reuse; no open-data licence was identified. This review does not determine whether citing individual factual values in an independently authored noncommercial visualization requires additional permission. It does not establish that such references are prohibited either. Broader reproduction of procedure data remains unverified.

No chart PDF, chart image or NATS branding is redistributed with this implementation. The sources are linked and the bounded factual references are distinguished from the authored trajectory. Source availability and correct interpretation do not certify operational applicability, professional training validity, obstacle clearance or flight performance.

The approach PDF was read as text and visually inspected. Its SHA-256 was recorded in the local reference-review receipt. Implementation and native-render acceptance must be recorded separately; reference inspection alone is not acceptance of the code or video.
