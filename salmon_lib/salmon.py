# This is all extremely WIP, and not in working state.
from salmon_lib.parsers import *
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

def with_default(main,higher,func):
        if isinstance(main, list):  #main is a list of tuples
            default = None
            done = []
            for rate in main:
                stock = rate[0]
            #    print('stock'+str(stock))
                if stock == "default":
                    default = rate[1]
                else:
                    done.append(stock)
                    func(stock,rate[1])

            for stock in higher:
                if stock.abbreviation in done:
                    pass
                else:
                    func(stock.abbreviation,default)

        elif isinstance(main, dict): # main is a dictionary
            default = main.get("default")
            done = []
            for stock, rate in main.items():
                if stock == "default":
                    pass
                else:
                    done.append(stock)
                    func(stock,rate)
            for stock in higher:
                if stock.abbreviation in done:
                    pass
                else:
                    func(stock.abbreviation,default)
        else:
            for stock in higher: # main is a single value
                func(stock.abbreviation,main)

def builder(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self

    return wrapper

"""
maximum_ocean_age
mature_age -> age when net catches are mature
natural_mortality -> natural mortality by age
incidental_mortality -> incidental mortality rate (troll,net,sport)
start_year -> sim start year
model_year -> model start year
end_year -> end year
"""
class Sim:
    def __init__(self,config=None):
        if config:
            self.__dict__ = config
        self.stocks = []
        self.fisheries = []
        self.maximum_ocean_age = self.__dict__.get('maximum_ocean_age',5)
        self.mature_age = self.__dict__.get('mature_age',4)
        self.natural_mortality = self.__dict__.get('natural_mortality',[0.5,0.4,0.3,0.2,0.1])
        self.incidental_mortality = self.__dict__.get('incidental_mortality',[0.3,0.9,0.3])
        self.model_year = self.__dict__.get('model_year',1979)
        self.start_year = self.__dict__.get('start_year',1995)
        self.end_year = self.__dict__.get('end_year',2017)
        # TODO: make this configurable via builder functions

    def build_fp(self):
        array = [[[[] for i in range(len(self.fisheries))] for j in range(len(self.stocks))] for k in range(len(self.stocks[0].policies))] # allocate array as long as the first stock's amount of defined years
        for i,stock in enumerate(self.stocks):
            for j,year in enumerate(stock.policies):
                array[j][i] = year
        return array

    def build_stk(self):
        abbreviations = []
        stocks = {}
        for stock in self.stocks:
            abbreviations.append(stock.abbreviation)
            stocks[stock.abbreviation] = {
                'cohort_abundance': stock.abundances,
                'maturation_rates': stock.maturation_rate,
                'adult_equivalent': stock.adult_equivalent,
                'fishery_exploitation': stock.rates
            }
        return (abbreviations,stocks)

#    bse = {
#        'number_of_stocks': int(lines[0]),
#        'maximum_ocean_age': int(lines[1]),
#        'number_of_fisheries': int(lines[2]),
#        'initial_year': int(lines[3]), # hardcoded at 1979, apparently?
#        'net_catche_maturity_age': int(lines[4]), # at line 5,
    def build_bse(self):
        bse = {
            'number_of_stocks': len(self.stocks),
            'number_of_fisheries': len(self.fisheries),
            'maximum_ocean_age': self.maximum_ocean_age,
            'initial_year': 1979,
            'net_catch_maturity_age': self.mature_age,
            'natural_mortality_by_age': self.natural_mortality,
            'incidental_mortality': self.incidental_mortality,
            'ocean_net_fisheries': [],
            'terminal_fisheries': [],
            'fisheries': [],
            'stocks': []
        }

        for fishery in self.fisheries:
            bse['fisheries'].append({'name':fishery.name,'proportions_non_vulnerable':fishery.proportions}) # proportions non vulnerable: ages 2,3,4,5
            bse['ocean_net_fisheries'].append(fishery.ocean_net)

        for stock in self.stocks:
            bse['terminal_fisheries'].append(stock.terminals)
            bse['stocks'].append({
                'name': stock.name,
                'id': stock.abbreviation,
                'production_param': stock.param,
                'msy_esc_estimate': stock.msy_esc,
                'msh_esc_flag': stock.msh_flag,
                'idl': stock.idl,
                'age_conversion': stock.age_factor,
                'hatchery_flag': stock.hatchery_flag
            })

        return bse

    def build_ev(self):
        ev = {
            'start_year': self.model_year,
            'end_year': self.end_year,
            'stocks': []
    #            {
            #        'log': ['Log', 'Normal', 'Indep', '-0.6343', '1.0916', '911'] # /shrug
        #            'years': [3.30215,0.532,3.3252] # scalars for each year
        #        },
    #        ]
        }
        for stock in self.stocks:
            ev['stocks'].append({'log':stock.log_p,'years': stock.ev_scalars})
        return ev

class FisheryBuilder:
    def __init__(self, sim, config=None):
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
    def terminal(self,terminal):
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
        with_default(self.exploitations,self.sim.stocks,lambda x,y: self.sim.stocks[self.stock_index(x)].exploitation(y))

        with_default(self.terminal,self.sim.stocks,lambda x,y: self.sim.stocks[self.stock_index(x)].terminal(y))

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
                    self.sim.stocks[self.stock_index(stock.abbreviation)].policy(i,year)

        self.sim.fisheries.append(self)
        return self.sim.fisheries[-1]


"""
attributes:
name
hatchery_n(ame)
abbreviation
hatchery_flag
msh_flag
msy_esc
param
idl
conversion_factor
smolt
smolt_changes
abundances
ev_scalars + log_p
maturation_rate(s)
adult_equivalent(s)
maturation_by_year
max_proportion
"""
class StockBuilder:
    def __init__(self, sim, config=None):
        # do something with config
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
    def hatchery_name(self,name):
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

    def terminal(self,flag):
        self.terminals.append(flag)

    def policy(self, year, list):
        if len(self.policies) <= year:
            self.policies += ([[]] * ((year + 1) - len(self.policies)))
    #    print("l" + str(list))
    #    print(self.policies)
        print(list)
        self.policies[year].append(list)
        print(self.policies)
    #    print('p' + str(self.policies))

    def build(self):
        self.sim.stocks.append(self)
        self.index = len(sim.stocks) - 1
        return self.sim.stocks[-1]

#sim = Sim()

#stock_config = {
#    'name': 'Salmon Institute SE',
#    'abbreviation': 'SIBR',
#    'cohort_abundance': [0.1,0.2,0.3,0.4],
#    'maturation_rate': [0.1,0.2,0.3,0.4],
#    'adult_equivalent': [0.1,0.2,0.3,0.4],
#    'ev_scalars': [0.20,0.30],
#    'log_p': ['Log', 'Normal', 'Indep', '-0.6343', '1.0916', '911'],
#    'hatchery_flag': True,
#    'msy_esc': 7400,
#    'msh_flag': True,
#    'idl': 1.0,
#    'param': 1.4,
#    'age_factor': 2.0
#}

#stock = StockBuilder(sim,config=stock_config).build()
#fishery = FisheryBuilder(sim).name("Society for Salmon").pnv(0.1,0.2,0.3,0.4).ocean(False).exploits([("SIBR",[4,3,2,1])]).policy([1.0,2.0]).terminal(True).build()
