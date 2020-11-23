import re

# not even gonna try to document the format for this one. perish
# jk this needs to be documented
stock_r = re.compile(
    "(.+)\s+,\s+(\d+[.]\d+)\s+(\d+)\s+(\d+[.]\d+)\s+(\d+)\s+(\d+)\s+,(.+)\s+,(\d+[.]\d+)"
)


def parse_bse(file):
    lines = file.readlines()
    bse = {
        "number_of_stocks": int(lines[0]),
        "maximum_ocean_age": int(lines[1]),
        "number_of_fisheries": int(lines[2]),
        "initial_year": int(lines[3]),  # hardcoded at 1979, apparently?
        "net_catch_maturity_age": int(lines[4]),  # at line 5,
        "natural_mortality_by_age": [],  # ages (1,2,3,4,5)
        "incidental_mortality": [],  # incidental_mortality rates for troll, net, sport
        "fisheries": [],
        "ocean_net_fisheries": [],  # this is a list of bools. true indicates an ocean net fishery. yeah idk either
        "terminal_fisheries": [],  # rows are stocks, containing a list of booleans. true indicates a terminal fishery. idk²
        "stocks": [],
    }

    j = 5
    for line in lines[5:]:
        try:
            float(line.split()[0])
            break
        except ValueError:
            j += 1
            bse["fisheries"].append(
                {"name": line.strip(), "proportions_non_vulnerable": []}
            )  # proportions non vulnerable: ages 2,3,4,5

    for i, line in enumerate(lines[j:]):
        row = line.strip().split()
        if len(row) != 4:
            break
        j += 1
        bse["fisheries"][i]["proportions_non_vulnerable"] = [float(s) for s in row]

    bse["natural_mortality_by_age"] = [float(s) for s in lines[j].split()]
    bse["incidental_mortality"] = [float(s) for s in lines[j + 1].split()]
    bse["ocean_net_fisheries"] = [bool(int(s)) for s in lines[j + 2].split()]
    j += 3

    for line in lines[j:]:
        row = line.strip().split()
        if not row[0].isdigit():
            break
        j += 1
        bse["terminal_fisheries"].append([bool(int(s)) for s in row])

    abbrevs = []
    for line in lines[j:]:
        match = stock_r.match(line.strip())
        bse["stocks"].append(
            {
                "name": match.group(1),  # Stock name
                "production_param": float(
                    match.group(2)
                ),  # Production parameter A Ricker A value for natural stocks Productivity for hatchery stocks
                "msy_esc_estimate": int(match.group(3)),  # Estimate of MSY escapement
                "idl": float(match.group(4)),  # IDLs for calibration runs only
                "hatchery_flag": bool(int(match.group(5))),  # Flag for hatchery stocks
                "msh_esc_flag": bool(
                    int(match.group(6))
                ),  # MSH escapement flag; true/1 truncates at maximum,  false/0 truncates at optimum
                "id": match.group(7),  # stock abbreviation
                "age_conversion": float(match.group(8)),  # age 2 to 1 conversion factor
            }
        )
        abbrevs.append(match.group(7))
    return (abbrevs, bse)

    bse = {
        "number_of_stocks": int(lines[0]),
        "maximum_ocean_age": int(lines[1]),
        "number_of_fisheries": int(lines[2]),
        "initial_year": int(lines[3]),  # hardcoded at 1979, apparently?
        "net_catch_maturity_age": int(lines[4]),  # at line 5,
        "natural_mortality_by_age": [],  # ages (1,2,3,4,5)
        "incidental_mortality": [],  # incidental_mortality rates for troll, net, sport
        "fisheries": [],
        "ocean_net_fisheries": [],  # this is a list of bools. true indicates an ocean net fishery. yeah idk either
        "terminal_fisheries": [],  # rows are stocks, containing a list of booleans. true indicates a terminal fishery. idk²
        "stocks": [],
    }


def write_bse(data, file):
    file.write(
        f"""
 {data['number_of_stocks']}
 {data['maximum_ocean_age']}
 {data['number_of_fisheries']}
 {data['initial_year']}
 {data['net_catch_maturity_age']}\n"""[
            1:
        ]
    )

    for fishery in data["fisheries"]:
        file.write(f"{fishery['name']}\n")

    for fishery in data["fisheries"]:
        for scalar in fishery["proportions_non_vulnerable"]:
            file.write(f"{scalar:7.5f}  ")
        file.write("\n")

    for mortality in data["natural_mortality_by_age"]:
        file.write(f"{mortality:3.1f} ")
    file.write("\n")

    for mortality in data["incidental_mortality"]:
        file.write(f"{mortality:3.1f} ")
    file.write("\n")

    for mortality in data["ocean_net_fisheries"]:
        file.write(f"{int(mortality)}  ")
    file.write("\n")

    for terminal_row in data["terminal_fisheries"]:
        for terminal_flag in terminal_row:
            file.write(f"{int(terminal_flag)}  ")
        file.write("\n")

    for stock in data["stocks"]:
        file.write(
            f"{stock['name']} , {stock['production_param']:5.3f}    {stock['msy_esc_estimate']}  {stock['idl']:4.2f}   {int(stock['hatchery_flag'])}  {int(stock['msh_esc_flag'])}  ,{stock['id']} ,{stock['age_conversion']:7.5f}"
        )
        file.write("\n")


"""
{
    'AKS': {
        'cohort_abundance': [16082.775, 8841.0469, 4265.1133, 722.23273], # Initial cohort abundance (age 2, 3, 4, and 5)
        'maturation_rates': [0.053398825, 0.14530915, 0.69034618, 1.0000001], # Maturation rates (age 2, 3, 4, and 5)
        'adult_equivalent': [0.58872306, 0.80788922, 0.96903467, 1.0000001], # Adult equivalent factors (age 2, 3, 4, and 5)
        'fishery_exploitation': [ # Fishery exploitation rates. Columns are ages (2, 3, 4, and 5) and rowsare fisheries.
            [0.0, 0.41631317, 0.24833483, 0.25773025],
            ...
        ]
    },
    ...
}
"""


def parse_stk(file):
    stocks = {}
    curr_stock = ""
    for line in file:
        row = line.split()
        try:
            float(row[0])
            stocks[curr_stock]["fishery_exploitation"].append([float(s) for s in row])
        except ValueError:
            curr_stock = row[0]
            stocks[curr_stock] = {
                "cohort_abundance": [float(s) for s in next(file).split()],
                "maturation_rates": [float(s) for s in next(file).split()],
                "adult_equivalent": [float(s) for s in next(file).split()],
                "fishery_exploitation": [],
            }
    return stocks


# this requires the order of the stock ids, from the .bse files
def write_stk(abbrevs, data, file):
    for sid in abbrevs:
        stock = data[sid]
        file.write(f"{sid}\n")
        for a in stock["cohort_abundance"]:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for a in stock["maturation_rates"]:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for a in stock["adult_equivalent"]:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for fishery in stock["fishery_exploitation"]:
            for a in fishery:
                file.write(f"{a:12.8E}  ")
            file.write("\n")
