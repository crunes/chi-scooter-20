## Mapping Chicago's 2020 E-Scooter Pilot

### Background
On August 12, the Chicago Department of Transportation (CDOT) and the Department of Business Affairs and Consumer Protection (BACP) launched a second, four-month electric-scooter pilot program that "includes enhanced requirements to keep sidewalks and the right of way clear of obstructions, and ensures equitable distribution of scooters throughout the City." This second pilot includes 10,000 scooters divided equally among three vendors: Bird, Lime and Spin.

"The second pilot requires the vendors to deploy at least half their fleets in Priority Areas that cover 43% of the total pilot area. The equity priority areas cover neighborhoods where residents face systemic disadvantages following generations of underinvestment and inequitable access to transportation and other resources. Compliance to this requirement will be checked twice per day. Vendors will provide the City with real-time data on operations, ridership, and safety, and the City may suspend or revoke the licenses of vendors that fail to adhere to the pilot’s terms."

Read the full press release [here](https://www.chicago.gov/city/en/depts/cdot/provdrs/bike/news/2020/august/city-of-chicago-launches-2020-shared-e-scooter-pilot-program-wit.html).

### Analysis
This Jupyter Notebook maps Bird and Lime fleets to visualize where the scooters are and if they comply with having half their fleets in Priority Areas, shown on [this map](https://www.chicago.gov/content/dam/city/depts/cdot/Misc/EScooters/2020/Chicago%202020%20E-Scooter%20Pilot%20Map.pdf). I downloaded the [Equity Priority Area](https://data.cityofchicago.org/Transportation/E-scooter-Priority-Area-2020/99tm-6k6i) GeoJSON file and saved it to my `data` directory because I assume this area will not change and the API is for the JSON file, not the GeoJSON file.

As of 7 AM on September 6, 2020, Lime had 50 percent of its fleet within the Equity Priority Area but Bird did not meet this requirement.

### Next Steps
Unfortunately, for legal reasons, the team had to pause all analysis using vendors' live data feeds. If you're interested in looking at the data, head to the [Chicago Data Portal](https://data.cityofchicago.org/browse?tags=e-scooter) for all (or most) of your open data needs!
