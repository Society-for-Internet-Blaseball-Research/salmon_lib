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

The actual base.cei file looks different mainly in whitespace...

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
        "fishery": []
    }

    # now for the fun stuff. From some file-surgery testing, I believe that
    # CRiSP Harvest expects a comment line before each fishery, and skips it.
    # Next, it requires a line the fishery ID number. Then, it requires one
    # line for every year from start_base to the end of ceil_change_years.
    # I think. Or, uh...well, let's just say for now that it expects the end of
    # ceil_change_years to be the last year listed.
    i = 7
    while i < len(lines):
        i += 1
        # it's too late to write code. notes: go through and populate a dict?
        # fishery = {
        # id = (int),
        # years = [{year: int, catch: int, note: str}, ...]
        # num_force: int,
        # years_force: [list of ints, len=num_force]
        # }
    return cei
