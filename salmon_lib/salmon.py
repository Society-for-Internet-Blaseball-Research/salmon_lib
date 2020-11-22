# This is all extremely WIP, and not in working state.
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
"""


def builder(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self

    return wrapper


class Sim:
    def __init__(self):
        self.stocks = []
        self.fisheries = []


class FisheryBuilder:
    def __init__(self, sim, config=None):
        self.sim = sim

    @builder
    def name(self, name):
        self.name = name

    @builder
    def ocean_net(self, flag):
        self.ocean_net = flag

    @builder
    def pnv(self, proportions):
        if isinstance(argv[0], list):
            self.proportions = list
        elif isinstance(argv[0], tuple):
            self.proportions = list(argv[0])
        else:
            self.proportions = argv

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
        if isinstance(self.exploitations, list):
            for rate in self.exploitations:
                stock_index = self.stock_index(rate[0])
                self.sim.stocks[stock_index].exploitation(rate[1])

        elif isinstance(self.exploitations, dict):
            for stock, rate in self.exploitation:
                stock_index = self.stock_index(stock)
                self.sim.stocks[stock_index].exploitation(rate)

        for i, year in enumerate(self.policy):
            if isinstance(year, list):  # year is a list of tuples
                default = None
                done = []
                for rate in year:
                    stock = rate[0]
                    print(stock)
                    if stock == "default":
                        default = rate[1]
                    else:
                        done.append(stock)
                        stock_index = self.stock_index(stock)
                        self.sim.stocks[stock_index].policy(i, rate[1])

                for stock in sim.stocks:
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
                for stock in sim.stocks:
                    if stock.abbreviation in done:
                        pass
                    else:
                        stock.policy(i, default)
            elif isinstance(year, float):  # year is a single float
                for stock in sim.stocks:
                    self.sim.stocks[stock_index].policy(i, year)

        sim.fisheries.append(self)


class StockBuilder:
    def __init__(self, sim, config=None):
        # do something with config
        self.rates = []
        self.policies = []
        self.sim = sim

    @builder
    def name(self, name):
        self.name = name

    @builder
    def abbrev(self, abbrev):
        self.abbreviation = abbrev

    @builder
    def hatchery(self, flag):
        self.hatchery = flag

    @builder
    def msh(self, flag):
        self.msh = flag

    @builder
    def msy(self, estimate):
        self.msy = estimate

    @builder
    def production_a(self, param):
        self.param = param

    @builder
    def calibration_idl(self, idl):
        self.idl = idl

    @builder
    def conversion_factor(self, factor):
        self.conversion_factor = factor

    @builder
    def cohort_abundances(self, *argv):
        if isinstance(argv[0], list):
            self.abundances = list
        elif isinstance(argv[0], tuple):
            self.abundances = list(argv[0])
        else:
            self.abundances = argv

    @builder
    def maturation_rates(self, *argv):
        if isinstance(argv[0], list):
            self.maturation_rates = list
        elif isinstance(argv[0], tuple):
            self.maturation_rates = list(argv[0])
        else:
            self.maturation_rates = argv

    @builder
    def adult_equivalents(self, *argv):
        if isinstance(argv[0], list):
            self.adult_equivalents = list
        elif isinstance(argv[0], tuple):
            self.adult_equivalents = list(argv[0])
        else:
            self.adult_equivalents = argv

    @builder
    def evs(self, evs):
        if isinstance(evs, list):
            self.evs = list
        elif isinstance(evs, dict):
            self.evs = [v for k, v in sorted(evs.items())]

    @builder
    def log(self, *argv):
        if isinstance(argv[0], list):
            self.log = list
        elif isinstance(argv[0], tuple):
            self.log = list(argv[0])
        else:
            self.log = argv

    @builder
    def maturation_by_year(self, *argv):
        if isinstance(argv[0], list):
            self.maturation_by_year = list
        elif isinstance(argv[0], tuple):
            self.maturation_by_year = list(argv[0])
        else:
            self.maturation_by_year = argv

    @builder
    def smolt_survival(self, smolt):
        self.smolt = smolt

    @builder
    def maximum_proportion(self, proportion):
        self.maximum_proportion = proportion

    @builder
    def smolt_changes(self, *argv):
        if isinstance(argv[0], list):
            self.smolt_changes = list
        elif isinstance(argv[0], tuple):
            self.smolt_changes = list(argv[0])
        else:
            self.smolt_changes = argv

    def exploitation(self, list):
        self.rates.append(list)

    def policy(self, year, list):
        if len(self.policies) <= year:
            self.policies += [[]] * ((year + 1) - len(self.policies))
        self.policies[year].append(list)

    def build(self):
        self.sim.stocks.append(self)
        self.index = len(sim.stocks) - 1
        return self.sim.stocks[-1]
