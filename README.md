# salmon_lib
### A library to read and write CRiSP Harvest Model files
**[A SIBR Project](https://sibr.dev)** <br />
*Born out of [the saga of salmon steve](https://salmon.sibr.dev/steve.html)*
<br />

![Screenshot of the CRiSP Harvest v3.0.6 user interface. Its traced map of the Pacific Northwest has been replaced with an overly detailed render of all of North America, Japan, and Hawai'i. There are little ship icons demarking the locations of assorted blaseball teams. The Canada Moist Talkers are missing from Halifax, for some reason.](https://salmon.sibr.dev/crisp_blaseball.png)

### Tools
**crisp_map** - builds a CRiSP map file from svg data
(requires installing dependencies with `pip install -r requirements.txt`)
```
Usage:
  python -m salmon_lib.crisp_map > map.dat

If you want to display the map in the CRiSP Harvest Simulator Simulator:
  python -m salmon_lib.crisp_map display
```
**bound_patcher** - patches lat/long bounds in CRiSP
```
Usage:
  python -m salmon_lib.bound_patcher
```

### Credits & contributors
- **[The CRiSP Harvest Team](http://www.cbr.washington.edu/analysis/archive/harvest/crispharvest)**
- **[ubuntor](https://github.com/ubuntor), zhp module, map bound patcher**
- **[alisww](https://github.com/alisww), parsers+writers**
- **[robbyblum](https://github.com/robbyblum), fp parser+writer**
- **[dannybd](https://github.com/dannybd), CRiSP map data, parser, and CRiSP Harvest Simulator Simulator**

### Features & TODOs
**TODO**
- add more syntactic sugar

**Implemented files & formats**
- `map.dat` (see `crisp_map.py`)
- `.opt`
- `.mat`
- `.evo`
- `.stk`
- `.zhp`
- `.bse`
- `.idl`
- `.enh`
- `.prn` (read-only)

**missing formats**
- `.cei` (in progress)
- `.config`
- `.monte`
