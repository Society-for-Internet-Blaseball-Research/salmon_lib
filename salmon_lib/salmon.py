# This is all extremely WIP, and not in working state.
from salmon_lib.parsers import *
import os
import os.path
import tempfile
import subprocess
import shutil
import glob
import json
import time
import statistics

"""
## .bse:
- Name
- Abbreviation
- Index (just by the order stocks are specified in)
- Production parameter A (can be set by year (.enh files))
- Msy escapement estimate
- Idl for calibration
- Flag for hatchery
- Msh escapement flag
- Age 2 to 1 conversion factor
- Terminal fisheries per stock

### .stk:
- Initial cohort abundance (ages 2, 3, 4, 5)
- Maturation rates (2, 3, 4, 5)
- Adult equivalent factors (2, 3, 4, 5)
- Exploitation rates for fisheries (ages 2, 3, 4, 5) <- this is kinda part of fisheries too. crisp do be like this

### .ev/.evo:
- EV scalars per year

## Optional?
### .idl:
- Idl scalars per year

### .msc:
- Abbreviation + name
- Used in conjunction with .mat

### .mat:
- Maturation rates per year (ages 2, 3, 4)
- Adult equivalent factors per year (ages 2, 3, 4)

### .enh:
- Smolt to age 1 survival rate
- Maximum proportion of spawners used for broodstock
- Smolt production changes from base period (by brood year)

## Fishery Parameters

### .bse
- Name
- Index
- Proportions non-vulnerable (ages 2, 3, 4, 5)
- Terminal flag (per stock)
- Is ocean net fishery

### .pnv
- Proportions non-vulnerable (ages 2, 3, 4, 5) by year

### .fp
- Fishery Policy (Harvest Rate) scalars
by year and by stock

### Missing files
- .cei

Salmon Stlats / File

catch -> ?cat.prn; by fishery?
abundances indices -> ?abd.prn; by fishery
escapement -> ?esc.prn; by stock
term run -> ?trm.prn; by stock?
ocn exploitation rate statistics -> ?ohr.prn; by stock
total exploitation rates -> ?thr.prn; by stock
incidental mortality rates -> ?lim.prn, ?sim.prn, ?tim.prn; by fishery?
TOTAL MORTALITIES BY STOCK & FISHERY - > ?[stock abbreviation].prn
stock prop -> none?
rt -> ?rt.prn 
the rest of the report section is ???
harvest rate -> possibly ?coh.prn and i just missed it. the code is better at generating configs than me, frankly
something -> ?trn.prn
"""


def with_default(main, higher, func):
    if isinstance(main, list):  # main is a list of tuples
        default = None
        done = []
        for rate in main:
            stock = rate[0]
            #    print('stock'+str(stock))
            if stock == "default":
                default = rate[1]
            else:
                done.append(stock)
                func(stock, rate[1])

        for stock in higher:
            if stock.abbreviation in done:
                pass
            else:
                func(stock.abbreviation, default)

    elif isinstance(main, dict):  # main is a dictionary
        default = main.get("default")
        done = []
        for stock, rate in main.items():
            if stock == "default":
                pass
            else:
                done.append(stock)
                func(stock, rate)
        for stock in higher:
            if stock.abbreviation in done:
                pass
            else:
                func(stock.abbreviation, default)
    else:
        for stock in higher:  # main is a single value
            func(stock.abbreviation, main)


def builder(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self

    return wrapper


class Sim:
    def __init__(self, config=None):
        """
        maximum_ocean_age
        mature_age -> age when net catches are mature
        natural_mortality -> natural mortality by age
        incidental_mortality -> incidental mortality rate (troll,net,sport)
        start_year -> sim start year
        model_year -> model start year
        end_year -> end year
        """

        if config:
            self.__dict__ = config

        self.stocks = []
        self.fisheries = []

        self.maximum_ocean_age = self.__dict__.get("maximum_ocean_age", 5)
        self.mature_age = self.__dict__.get("mature_age", 4)
        self.natural_mortality = self.__dict__.get(
            "natural_mortality", [0.5, 0.4, 0.3, 0.2, 0.1]
        )
        self.incidental_mortality = self.__dict__.get(
            "incidental_mortality", [0.3, 0.9, 0.3]
        )
        self.model_year = self.__dict__.get("model_year", 1979)
        self.start_year = self.__dict__.get("start_year", 1995)
        self.end_year = self.__dict__.get("end_year", 2017)
        # TODO: make this configurable via builder functions

    # JSON/Dict SIBR CRiSP Configuration. this is a friendlier encoding of CRiSP data we built
    def from_sibr_conf(self, data):
        self.__dict__ = data["sim"]
        self.stocks = []
        self.fisheries = []
        for stock in data["stocks"]:
            Stock(self, config=stock).build()
        for fishery in data["fisheries"]:
            Fishery(self, config=fishery).build()

    def to_sibr_conf(self):
        return {
            "sim": {
                "maximum_ocean_age": self.maximum_ocean_age,
                "mature_age": self.mature_age,
                "natural_mortality": self.natural_mortality,
                "incidental_mortality": self.incidental_mortality,
                "model_year": self.model_year,
                "start_year": self.start_year,
                "end_year": self.end_year,
            },
            "fisheries": self.fisheries,
            "stocks": self.stocks,
        }

    # runs a CRiSP simulation and fetch the results
    def run(self, crisp_path, wine_path="wine"):
        dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(dir, "input"))
        config = {
            "model_start_year": self.model_year,
            "sim_start_year": self.start_year,
            "end_year": self.end_year,
            "calibration": False,
            "use_9525_evs": 1,
            "minimum_terminal_age": 3,
            "additional_slcm": False,
            "in_river": False,
            "input": {
                "base": "input/base.bse",
                "stock": "input/base.stk",
                "maturation": "input/base.msc",
                "ev": "input/base.ev",
                "idl": {"enable": False, "file": ""},
                "enh": "",
                "cnr": {"number": 0, "file": ""},
                "pnv": {"changes": 0, "files": [""]},
                "fp": "input/base.fp",
                "cei": {"enable": False, "file": ""},
                "monte": {"enable": False, "file": ""},
            },
            "output": {
                "enable": True,
                "prefix": "salmon",
                "catch": True,
                "term_run": True,
                "escapement": True,
                "ocn": 1,
                "exploitation": 1,
                "mortalities": 1,
                "incidental_mortality": True,
                "abundance": {
                    "number": len(self.fisheries),
                    "fisheries": [x for x in range(1, len(self.fisheries) + 1)],
                },
            },
            "report": {
                "header": "header",
                "stock_prop": False,
                "rt": True,
                "catch": False,
                "stock_fishery": 0,
                "shaker": False,
                "terminal_catch": False,
                "escapement": False,
                "harvest_rate": "N",
                "compare_base_year": False,
                "document_model": False,
                "stocks_enhancement": 0,  # reminder for alis, from alis: this move this to main category dumbass
                "density_dependence": False,
            },
        }

        with open(os.path.join(dir, "proto.OPT"), "w", newline="\r\n") as f:
            write_config(config, f)
        with open(os.path.join(dir, "input/base.fp"), "w", newline="\r\n") as f:
            write_fp(self.build_fp(), f)
        with open(os.path.join(dir, "input/base.stk"), "w", newline="\r\n") as f:
            stk = self.build_stk()
            write_stk(stk[0], stk[1], f)
        with open(os.path.join(dir, "input/base.bse"), "w", newline="\r\n") as f:
            write_bse(self.build_bse(), f)
        with open(os.path.join(dir, "input/base.ev"), "w", newline="\r\n") as f:
            write_evo(self.build_ev(), f)
        with open(os.path.join(dir, "input/base.msc"), "w", newline="\r\n") as f:
            write_msc(self.build_msc(), f)
        with open(os.path.join(dir, "input/base.mat"), "w", newline="\r\n") as f:
            write_mat(self.build_mat(), f)

        res = subprocess.run([wine_path, crisp_path, "-n"], cwd=dir)

        results = {
            "catch": self.load_prn(os.path.join(dir, "salmoncat.prn"), by_fishery=True),
            "abundances": self.load_abd(os.path.join(dir, "salmonabd.prn")),
            "esc": self.load_prn(os.path.join(dir, "salmonesc.prn")),
            "trm": self.load_prn(os.path.join(dir, "salmontrm.prn")),
            "ohr": self.load_prn(os.path.join(dir, "salmonohr.prn")),
            "lim": self.load_prn(os.path.join(dir, "salmonlim.prn"), by_fishery=True),
            "sim": self.load_prn(os.path.join(dir, "salmonsim.prn"), by_fishery=True),
            "tim": self.load_prn(os.path.join(dir, "salmontim.prn"), by_fishery=True),
            "rt": self.load_rt(os.path.join(dir, "salmonrt.prn")),
            "coh": self.load_abd(os.path.join(dir, "salmoncoh.prn")),
            "thr": self.load_prn(os.path.join(dir, "salmonthr.prn")),
            "stocks": {},
        }

        known = [
            "salmoncat.prn",
            "salmonabd.prn",
            "salmonesc.prn",
            "salmontrm.prn",
            "salmonohr.prn",
            "salmonlim.prn",
            "salmonsim.prn",
            "salmontim.prn",
            "salmonrt.prn",
            "salmoncoh.prn",
            "salmonthr.prn",
        ]

        for prn in glob.glob(dir + "/*.prn", recursive=False):
            if not os.path.basename(prn) in known:
                id = os.path.basename(prn)[6:9]
                results["stocks"][id] = self.load_stock(prn)
        shutil.rmtree(dir)
        return (res, results)

    # utility methods

    def build_fp(self):
        array = [
            [[[] for i in range(len(self.fisheries))] for j in range(len(self.stocks))]
            for k in range(len(self.stocks[0].policies))
        ]  # allocate array as long as the first stock's amount of defined years
        for i, stock in enumerate(self.stocks):
            for j, year in enumerate(stock.policies):
                array[j][i] = year
        return array

    def build_stk(self):
        abbreviations = []
        stocks = {}
        for stock in self.stocks:
            abbreviations.append(stock.abbreviation)
            stocks[stock.abbreviation] = {
                "cohort_abundance": stock.cohort_abundance,
                "maturation_rates": stock.maturation_rate,
                "adult_equivalent": stock.adult_equivalent,
                "fishery_exploitation": stock.rates,
            }
        return (abbreviations, stocks)

    def build_bse(self):
        bse = {
            "number_of_stocks": len(self.stocks),
            "number_of_fisheries": len(self.fisheries),
            "maximum_ocean_age": self.maximum_ocean_age,
            "initial_year": 1979,
            "net_catch_maturity_age": self.mature_age,
            "natural_mortality_by_age": self.natural_mortality,
            "incidental_mortality": self.incidental_mortality,
            "ocean_net_fisheries": [],
            "terminal_fisheries": [],
            "fisheries": [],
            "stocks": [],
        }

        for fishery in self.fisheries:
            bse["fisheries"].append(
                {
                    "name": fishery.name,
                    "proportions_non_vulnerable": fishery.proportions,
                }
            )  # proportions non vulnerable: ages 2,3,4,5
            bse["ocean_net_fisheries"].append(fishery.ocean_net)

        for stock in self.stocks:
            bse["terminal_fisheries"].append(stock.terminals)
            bse["stocks"].append(
                {
                    "name": stock.name,
                    "id": stock.abbreviation,
                    "production_param": stock.param,
                    "msy_esc_estimate": stock.msy_esc,
                    "msh_esc_flag": stock.msh_flag,
                    "idl": stock.idl,
                    "age_conversion": stock.age_factor,
                    "hatchery_flag": stock.hatchery_flag,
                }
            )

        return bse

    def build_ev(self):
        ev = {"start_year": self.model_year, "end_year": self.end_year, "stocks": []}

        for stock in self.stocks:
            ev["stocks"].append({"log": stock.log_p, "years": stock.ev_scalars})
        return ev

    def build_msc(self):
        return {
            "maturation_file": "input/base.mat",
            "stocks": [
                (stock.abbreviation, stock.hatchery_n)
                for stock in self.stocks
                if len(stock.hatchery_n) > 0
            ],
        }

    # this is kind of hack
    def build_mat(self):
        years = {}
        for stock in self.stocks:
            if stock.hatchery:
                for i, year in enumerate(stock.maturation_by_year):
                    if not (1979 + i) in years:
                        years[1979 + i] = {}
                    years[1979 + i][stock.abbreviation] = {
                        2: year[0],
                        3: year[1],
                        4: year[2],
                    }

        return years

    def load_prn(self, file, by_fishery=False):
        if os.path.isfile(file):
            with open(file) as f:
                parsed = parse_prn(f)
                results = {}
                for k, v in parsed.items():
                    name = (
                        self.fisheries[k].name
                        if by_fishery
                        else self.stocks[k].abbreviation
                    )
                    results[name] = v
                return results

        else:
            return None

    def load_rt(self, file):
        if os.path.isfile(file):
            with open(file) as f:
                return parse_rt(f)
        else:
            return None

    def load_abd(self, file):
        if os.path.isfile(file):
            with open(file) as f:
                return parse_abd(f)
        else:
            return None

    def load_stock(self, file):
        if os.path.isfile(file):
            with open(file) as f:
                res = {}
                stks = parse_stock_file(f)
                for k, v in stks.items():
                    res[self.fisheries[k].name] = v
                return res
        else:
            return None


class Fishery:
    def __init__(self, sim, config=None):
        """
        attributes
        name -> uh
        ocean_net -> is an ocean net fishery
        exploits -> exploitation rates per stock
        terminal -> is terminal fishery for x stock
        policy -> "detailed Fishery Policy (Harvest Rate) scalars that alter the impact of a given fishery on the stocks on a year-by-year basis."
        pnv - > proportions non vulnerable (by year is TODO)
        """
        if config:
            self.__dict__ = config
        self.sim = sim

    @builder
    def name(self, name):
        self.name = name

    @builder
    def ocean(self, flag):
        self.ocean_net = flag

    @builder
    def pnv(self, *argv):
        if isinstance(argv[0], list):
            self.proportions = list
        elif isinstance(argv[0], tuple):
            self.proportions = list(argv[0])
        else:
            self.proportions = list(argv)

    """
    [
        ('AKS',[rates])
    ]
    or
    {
        'AKS': [rates]
    }
    """

    # both of these get straightened out in .build()
    @builder
    def exploits(self, exploitations):
        self.exploitations = exploitations

    @builder
    def terminal(self, terminal):
        self.terminal = terminal

    """
    [ # years
        [
            ('AKS',scalar),
            ...
        ]
    ]

    [ # years
        {
            'AKS': scalar
        }
    ]

    [ # years
        1.0 # applies to all stocks
    ]
    """

    @builder
    def policy(self, policy):
        self.policy = policy

    def stock_index(self, stock):
        return next(i for i, x in enumerate(self.sim.stocks) if x.abbreviation == stock)

    def build(self):
        with_default(
            self.exploitations,
            self.sim.stocks,
            lambda x, y: self.sim.stocks[self.stock_index(x)].exploitation(y),
        )

        with_default(
            self.terminal,
            self.sim.stocks,
            lambda x, y: self.sim.stocks[self.stock_index(x)].terminal(y),
        )

        for i, year in enumerate(self.policy):
            if isinstance(year, list):  # year is a list of tuples
                default = None
                done = []
                for rate in year:
                    stock = rate[0]
                    #    print('stock'+str(stock))
                    if stock == "default":
                        default = rate[1]
                    else:
                        done.append(stock)
                        stock_index = self.stock_index(stock)
                        self.sim.stocks[stock_index].policy(i, rate[1])

                for stock in self.sim.stocks:
                    if stock.abbreviation in done:
                        pass
                    else:
                        stock.policy(i, default)
            elif isinstance(year, dict):  # year is a dictionary
                default = year.get("default")
                done = []
                for stock, rate in enumerate(year):
                    if stock == "default":
                        pass
                    else:
                        self.done.append(stock)
                        stock_index = stock_index(stock)
                        self.sim.stocks[stock_index].policy(i, rate)
                for stock in self.sim.stocks:
                    if stock.abbreviation in done:
                        pass
                    else:
                        stock.policy(i, default)
            elif isinstance(year, float):  # year is a single float
                for stock in sim.stocks:
                    self.sim.stocks[self.stock_index(stock.abbreviation)].policy(
                        i, year
                    )

        self.sim.fisheries.append(self)
        return self.sim.fisheries[-1]


class Stock:
    def __init__(self, sim, config=None):
        """
        attributes:
        name -> stock name
        hatchery_n(ame) -> name for stock hatchery
        abbreviation -> stock abbreviation
        hatchery_flag -> is hatchery
        msh_flag -> msh escapement flag - 1 truncates at max, 0 truncates at optimum
        msy_esc -> estimate of msy escapement
        param -> production parameter A
        idl -> inter-dam-loss rate for calibration runs
        conversion_factor -> age 2 to 1 conversion factor
        smolt -> smolt to age 1 survival
        smolt_changes -> smolt to age 1 survival rate
        abundances -> initial cohort abundances (ages 2, 3, 4, 5)
        maturation_rate(s) -> maturation rates (ages 2, 3, 4, 5)
        adult_equivalent(s) -> adult equivalent factors (ages 2, 3, 4, 5)
        maturation_by_year -> maturation rates (ages 2, 3, 4) per year + adult equivalent factors (ages 2, 3, 4) per year
        ev_scalars + log_p -> environmental variability scalars + logarithmic stuff (for monte carlo sim)
        max_proportion -> Maximum proportion of spawners that can be used forbroodstock (used for supplementation)
        """
        if config:
            self.__dict__ = config
        self.rates = []
        self.policies = []
        self.terminals = []
        self.sim = sim

    @builder
    def name(self, name):
        self.name = name

    @builder
    def hatchery_name(self, name):
        self.hatchery_n = name

    @builder
    def abbrev(self, abbrev):
        self.abbreviation = abbrev

    @builder
    def hatchery(self, flag):
        self.hatchery_flag = flag

    @builder
    def msh(self, flag):
        self.msh_flag = flag

    @builder
    def msy(self, estimate):
        self.msy_esc = estimate

    @builder
    def production_a(self, param):
        self.param = param

    @builder
    def calibration_idl(self, idl):
        self.idl = idl

    @builder
    def conversion_factor(self, factor):
        self.age_factor = factor

    @builder
    def cohort_abundances(self, *argv):
        if isinstance(argv[0], list):
            self.abundances = list
        elif isinstance(argv[0], tuple):
            self.abundances = list(argv[0])
        else:
            self.abundances = list(argv)

    @builder
    def maturation_rates(self, *argv):
        if isinstance(argv[0], list):
            self.maturation_rate = list
        elif isinstance(argv[0], tuple):
            self.maturation_rate = list(argv[0])
        else:
            self.maturation_rate = list(argv)

    @builder
    def adult_equivalents(self, *argv):
        if isinstance(argv[0], list):
            self.adult_equivalent = list
        elif isinstance(argv[0], tuple):
            self.adult_equivalent = list(argv[0])
        else:
            self.adult_equivalent = list(argv)

    @builder
    def evs(self, evs):
        if isinstance(evs, list):
            self.ev_scalars = list
        elif isinstance(evs, dict):
            self.ev_scalars = [v for k, v in sorted(evs.items())]

    @builder
    def log(self, *argv):
        if isinstance(argv[0], list):
            self.log_p = list
        elif isinstance(argv[0], tuple):
            self.log_p = list(argv[0])
        else:
            self.log_p = list(argv)

    @builder
    def maturation_by_year(self, *argv):
        """
        [ # years
            (241,532), # rate, equivalent for age 2
            (241,532), # age 3
            (241,532) # age 4
        ]
        """
        if isinstance(argv[0], list):
            self.maturation_by_year = list
        elif isinstance(argv[0], tuple):
            self.maturation_by_year = list(argv[0])
        else:
            self.maturation_by_year = list(argv)

    @builder
    def smolt_survival(self, smolt):
        self.smolt = smolt

    @builder
    def maximum_proportion(self, proportion):
        self.max_proportion = proportion

    @builder
    def smolt_changes(self, *argv):
        if isinstance(argv[0], list):
            self.smolt_changes = list
        elif isinstance(argv[0], tuple):
            self.smolt_changes = list(argv[0])
        else:
            self.smolt_changes = list(argv)

    def exploitation(self, list):
        self.rates.append(list)

    def terminal(self, flag):
        self.terminals.append(flag)

    def policy(self, year, list):
        if len(self.policies) <= year:
            self.policies += [[]] * ((year + 1) - len(self.policies))
        self.policies[year].append(list)

    def build(self):
        self.sim.stocks.append(self)
        self.index = len(self.sim.stocks) - 1
        return self.sim.stocks[-1]


# if __name__ == "__main__":
#     env_times = []
#     sim_times = []
#     fetch_times = []
#     load_times = []
#     build_times = []
#     sim_totals = []

#     for x in range(0,10000):
#         print(f"Run {x}")
#         start = time.time()
#   with open('sibr.json') as f:
#     config = json.loads(f.read())
#     json_load = time.time()
#     sim = Sim()
#     sim.from_sibr_conf(config)
#     res = sim.run('')
#             json_build = time.time()

#             sim_end = time.time()

#             load_times.append(json_load - start)
#             build_times.append(json_build - json_load)
#             sim_totals.append(sim_end - json_build)
#             env_times.append(res[2][0])
#             sim_times.append(res[2][1])
#             fetch_times.append(res[2][2])

#     print(f"Env times: Avg {statistics.mean(env_times)}; Mean {statistics.median(sorted(env_times))}")
#     print(f"Sim Run times: Avg {statistics.mean(sim_times)}; Mean {statistics.median(sorted(sim_times))}")
#     print(f"Fetch times: Avg {statistics.mean(fetch_times)}; Mean {statistics.median(sorted(fetch_times))}")
#     print(f"Load times: Avg {statistics.mean(load_times)}; Mean {statistics.median(sorted(load_times))}")
#     print(f"Build times: Avg {statistics.mean(build_times)}; Mean {statistics.median(sorted(build_times))}")
