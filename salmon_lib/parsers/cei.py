"""
let's do this
this file is arcane. quoth the manual:

The *.cei files (see Fig. 2.11) is used to set catch ceilings which are the
primary means selected by the PSC to reduce stock exploitation rates. The *.cei
file is used: (1) to specify fisheries with ceilings; (2) to set ceiling levels
(catch levels); and (3) to allow you to force Model catches to equal the
ceiling.

Fig. 2.11 looks like this:

1979    ,       Start of base period
1984    ,       End of base period
1985    ,       First year of ceiling management
1998    ,       Last year for ceiling management
11      ,       Number of fisheries with ceilings
7       ,       Number of ceiling level changes
1986 1987 1988 1990 1991 1992 , years to change ceilings
.................. S.E. Alaska Troll (excluding hatchery add-ON)......
1       ,       1st Fishery Number
        338000  ,1979,catch
                ... continue for each year
        230712  ,1990,catch [sic: this is the number for 1991 in the real file]
        162995  ,1992, THROUGH LAST YEAR OF CLG MGMT
        8       ,Number of years to force ceilings
        1985 1986 1987 1988 1989 1990 1991 1992 , years to force
.................. (etc for remaining Fisheries)

The actual base.cei file looks different mainly in whitespace.
"""

"""
.cei data format for reading and writing:
{
    "start_base": 1979,
    "end_base": 1984,
    "start_ceil": 1985,
    "end_ceil": 2017,
    "num_ceil_fisheries": 16,
    "num_ceil_changes": 13,
    "ceil_change_years": [1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998],
    "fisheries": [
        {
            "header": "........... S.E. Alaska Troll (excluding hatchery add-ON)..."
            "id": 1
            "ceilings": [
                {
                    "year": 1979,
                    "ceiling": 338000,
                    "comment": "catch"
                },
                ...
            ]
            "num_force": 10,
            "years_force": [1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994]
        },
        ...
    ]
}
"""


def parse_cei(file):
    lines = file.readlines()
    cei = {
        "start_base": int(lines[0].split(",")[0].strip()),
        "end_base": int(lines[1].split(",")[0].strip()),
        "start_ceil": int(lines[2].split(",")[0].strip()),
        "end_ceil": int(lines[3].split(",")[0].strip()),
        "num_ceil_fisheries": int(lines[4].split(",")[0].strip()),
        "num_ceil_changes": int(lines[5].split(",")[0].strip()),
        "ceil_change_years": [int(year) for year in lines[6].split(",")[0].split()],
        "fisheries": [],
    }

    # now for the fun stuff. From some file-surgery testing, I believe that
    # CRiSP Harvest expects a comment line before each fishery, and skips it.
    # Next, it requires a line the fishery ID number. Then, it requires one
    # line for every year from start_base to the end of ceil_change_years.
    # I think. Or, uh...well, let's just say for now that it expects the end of
    # ceil_change_years to be the last year listed.

    finalyear = cei["ceil_change_years"][-1]
    line_i = 7  # time to step through painfully and build each fishery dict
    for fish_i in range(cei["num_ceil_fisheries"]):
        # get the header (for completeness) and the fishery ID
        fishery = {}
        fishery["header"] = lines[line_i].strip()
        line_i += 1
        # I'm throwing away the "Nth Fishery Number" comment. If that matters,
        # I'm going to be upset with this file format
        fishery["id"] = int(lines[line_i].split(",")[0].strip())
        line_i += 1

        # time to loop to get the catch ceiling list
        fishery["ceilings"] = []
        year = cei["start_base"]  # initialization default
        while year < finalyear:
            year = int(lines[line_i].split(",")[1].strip())
            ceiling = int(lines[line_i].split(",")[0].strip())
            comment = lines[line_i].split(",")[2].strip()
            fishery["ceilings"].append(
                {"year": year, "ceiling": ceiling, "comment": comment}
            )
            line_i += 1

        # get number of years to force ceilings
        fishery["num_force"] = int(lines[line_i].split(",")[0].strip())
        line_i += 1
        # get years to force ceilings
        fishery["years_force"] = [
            int(year) for year in lines[line_i].split(",")[0].split()
        ]
        line_i += 1

        cei["fisheries"].append(fishery)

    return cei


# now I get to make my own whitespace decisions. If you think they're bad,
# you should see the original base.cei file
def write_cei(data, file):
    file.write(f"{data['start_base']:<19}, Start of base period\n")
    file.write(f"{data['end_base']:<19}, End of base period\n")
    file.write(f"{data['start_ceil']:<19}, First year of ceiling management\n")
    file.write(f"{data['end_ceil']:<19}, Last year for ceiling management\n")
    file.write(f"{data['num_ceil_fisheries']:<19}, Number of fisheries with ceilings\n")
    file.write(f"{data['num_ceil_changes']:<19}, Number of ceiling level changes\n")
    file.write(
        " ".join([f"{year}" for year in data["ceil_change_years"]])
        + ", Years to change ceilings\n"
    )

    for fishery in data["fisheries"]:
        file.write(f"{fishery['header']}\n")
        file.write(f"{fishery['id']:<19}, Nth Fishery Number\n")
        for year in fishery["ceilings"]:
            file.write(f"{year['ceiling']:>8}  , {year['year']}, {year['comment']}\n")
        file.write(f"  {fishery['num_force']:<8}, Number of years to force ceilings\n")
        file.write(
            "  "
            + " ".join([f"{year}" for year in fishery["years_force"]])
            + ", Years to force ceilings\n"
        )
