# converts og CRiSP data to our version of pythonic CRiSP
# this is inefficient and bad but it works

from salmon_lib.parsers import *
import json

if __name__ == "__main__":
    bse = None
    stk = None
    msc = None
    mat = None
    evo = None
    fp = None
    with open("base.bse") as f:
        bse = parse_bse(f)[1]
    with open("base.stk") as f:
        stk = parse_stk(f)
    with open("base.msc") as f:
        msc = parse_msc(f)
    with open("base.mat") as f:
        mat = parse_mat(f)
    with open("base.evo") as f:
        evo = parse_evo(f)
    with open("base.fp") as f:
        fp = parse_fp(f)

    fisheries = []
    stocks = []

    def stock_index(stock):
        return next(i for i, x in enumerate(stocks) if x["abbreviation"] == stock)

    for i, fishery in enumerate(bse["fisheries"]):
        fisheries.append(
            {
                "name": fishery["name"],
                "proportions": fishery["proportions_non_vulnerable"],
                "ocean_net": bse["ocean_net_fisheries"][i],
                "terminal": [],
                "exploitations": [],
                "policy": [],
            }
        )

    for i, stock in enumerate(bse["stocks"]):
        stocks.append(
            {
                "name": stock["name"],
                "abbreviation": stock["id"],
                "hatchery_flag": stock["hatchery_flag"],
                "msh_flag": stock["msh_esc_flag"],
                "msy_esc": stock["msy_esc_estimate"],
                "age_factor": stock["age_conversion"],
                "idl": stock["idl"],
                "param": stock["production_param"],
                "maturation_by_year": [],
                "cohort_abundance": [],
                "hatchery_n": "",
            }
        )

    for f in fisheries:
        f["policy"] = [[] for j in range(39)]

    for i, terminal_row in enumerate(bse["terminal_fisheries"]):
        for j, flag in enumerate(terminal_row):
            fisheries[j]["terminal"].append((stocks[i]["abbreviation"], flag))

    for i, (name, stock) in enumerate(sorted(stk.items())):
        stocks[i]["maturation_rate"] = stock["maturation_rates"]
        stocks[i]["adult_equivalent"] = stock["adult_equivalent"]
        stocks[i]["cohort_abundance"] = stock["cohort_abundance"]

        for j, exploitations in enumerate(stock["fishery_exploitation"]):
            fisheries[j]["exploitations"].append((name, exploitations))

    for hatchery in msc["stocks"]:
        stocks[stock_index(hatchery[0])]["hatchery_n"] = hatchery[1]

    for y, year in mat.items():
        for hatchery, rates in year.items():
            data = [
                (rates[2][0], rates[2][1]),
                (rates[3][0], rates[3][1]),
                (rates[4][0], rates[4][1]),
            ]
            stocks[stock_index(hatchery)]["maturation_by_year"].append(data)

    for i, stock in enumerate(evo["stocks"]):
        stocks[i]["ev_scalars"] = stock["years"]
        stocks[i]["log_p"] = stock["log"]

    for i, year in enumerate(fp):
        for j, stock in enumerate(year):
            for f, policy in enumerate(stock):
                fisheries[f]["policy"][i].append((stocks[j]["abbreviation"], policy))

    sim = {
        "maximum_ocean_age": 5,
        "mature_age": 4,
        "natural_mortality": [0.5, 0.4, 0.3, 0.2, 0.1],
        "incidental_mortality": [0.3, 0.9, 0.3],
        "model_year": 1979,
        "start_year": 1995,
        "end_year": 2017,
    }

    sibr = json.dumps({"fisheries": fisheries, "stocks": stocks, "sim": sim})

    with open("sibr.json", "w") as f:
        f.write(sibr)
