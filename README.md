# salmon_lib
### A library to read and write CRiSP Harvest Model files
**[A SIBR Project](https://sibr.dev)** <br />
*Born out of [the saga of salmon steve](https://salmon.sibr.dev/steve.html)*
<br />

![Screenshot of the CRiSP Harvest v3.0.6 user interface. Its traced map of the Pacific Northwest has been replaced with an overly detailed render of all of North America, Japan, and Hawai'i. There are little ship icons demarking the locations of assorted blaseball teams. The Canada Moist Talkers are missing from Halifax, for some reason.](https://salmon.sibr.dev/crisp_blaseball.png)


### Credits & contributors
- **[The CRiSP Harvest Team](http://www.cbr.washington.edu/analysis/archive/harvest/crispharvest)**
- **[ubuntor](https://github.com/ubuntor), who wrote the zhp module**
- **[alisww](https://github.com/alisww), parsers+writers**
- **[dannybd](https://github.com/dannybd), CRiSP map data, parser, and CRiSP Harvest Simulator Simulator**

### Features & TODOs
**TODO**
- add more syntactic sugar

**Implemented files & formats**
- `map.dat` (see `build_crisp_map.py`)
- `.opt`
- `.mat`
- `.evo`
- `.stk`
- `.zhp`
- `.prn` (read-only)
- `.bse` (read-only)

**missing formats**
- `.fp`
- `.enh`
- `.cei`
- `.pnv`
- `.idl`
- `.config`
- `.monte`
