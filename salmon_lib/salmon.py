import pprint
import re
"""
{
    1989: [
        (fishery id, statistic),
        ...
    ],
    ...
}
"""
def parse_stock_file(file):
    cols = []
    years = {}
    for line in file:
        row = line.split()
        if row[0] == "Year":
            for fishery in row[1:]:
                cols.append(int(fishery))
        else:
            year = int(row[0])
            years[year] = []
            for i,rate in enumerate(row[1:]):
                years[year].append((cols[i],int(rate)))
    return years

def parse_prn(file):
    years = {}
    for line in file:
        row = line.split()
        year = int(row[0])
        years[year] = []
        for i,stlat in enumerate(row[1:]):
            years[year].append((i,int(stlat)))
    return years

"""
evo data format for writing/reading:
{
'start_year': 1979,
'end_year': 2017,
'stocks': [
    {
        'log': ['Log', 'Normal', 'Indep', '-0.6343', '1.0916', '911'] # /shrug
        'years': [3.30215,0.532,3.3252] # scalars for each year
    },
    ...
]
}
"""
def parse_evo(file):
    lines = file.readlines()
    evo = {
        "start_year":  int(lines[0].strip()),
        "end_year": int(lines[1].strip()),
        "stocks": []
    }
    for line in lines[2:]:
        row = line.split()
        stock_id = int(row[0])
        evo["stocks"].append({"years": [], "log": []})
        for (i,scalar) in enumerate(row[1:]):
            if scalar == "Log":
                evo["stocks"][stock_id-1]["log"] = row[i+1:]
                break
            else:
                evo["stocks"][stock_id-1]["years"].append(float(scalar))
    return evo

def write_evo(data,file):
    file.write(f" {data['start_year']}\n")
    file.write(f" {data['end_year']}\n")
    for (i,stock) in enumerate(data['stocks']):
        file.write(f"  {i+1} ")
        for year in stock["years"]:
            file.write(f"{year:E}  ")
        for thing in stock["log"]:
            file.write(f"{thing}  ")
        file.write("\n")



"""
mat data format
{
    1989: {
        'AKS': {
            2: (0.0534,0.1453) # age 2 (maturation rate, adult equivalent factor),
            3: (0.0534,0.1453), # same format for age 3,
            4: (0.0534,0.1453) # same format for age 4
        },
        ...
    },
    ...
}
"""
def parse_mat(file):
    years = {}
    curr_year = None
    for line in file:
        if not line.startswith("      "):
            curr_year = int(line)
            years[curr_year] = {}
        else:
            row = line.split()
            stock = row[0].replace(',','')
            years[curr_year][stock] = {
                2: (float(row[1]),float(row[2])),
                3: (float(row[3]),float(row[4])),
                4: (float(row[5]),float(row[6]))
            }
    return years

def write_mat(data,file):
    for yr, stocks in sorted(data.items()):
        file.write(f"{yr}\n")
        for name,stock in sorted(stocks.items()):
            file.write(f"      {name},     {stock[2][0]:6.4f}    {stock[2][1]:6.4f}    {stock[3][0]:6.4f}    {stock[3][1]:6.4f}    {stock[4][0]:6.4f}    {stock[4][1]:6.4f}\n")

# not even gonna try to document the format for this one. perish
stock_r = re.compile("(.+)\s+,\s+(\d+[.]\d+)\s+(\d+)\s+(\d+[.]\d+)\s+(\d+)\s+(\d+)\s+,(.+)\s+,(\d+[.]\d+)")
def parse_bse(file):
    lines = file.readlines()
    bse = {
        'number_of_stocks': int(lines[0]),
        'maximum_ocean_age': int(lines[1]),
        'number_of_fisheries': int(lines[2]),
        'initial_year': int(lines[3]), # hardcoded at 1979, apparently?
        'net_catche_maturity_age': int(lines[4]), # at line 5,
        'natural_mortality_by_age': [], # ages (1,2,3,4,5)
        'incidental_mortality': [], # incidental_mortality rates for troll, net, sport
        'fisheries': [],
        'ocean_net_fisheries': [], # this is a list of bools. true indicates an ocean net fishery. yeah idk either
        'terminal_fisheries': [], # rows are stocks, containing a list of booleans. true indicates a terminal fishery. idk²
        'stocks': []
    }

    j = 5
    for line in lines[5:]:
        try:
            float(line.split()[0])
            break
        except ValueError:
            j += 1
            bse['fisheries'].append({'name':line.strip(),'proportions_non_vulnerable':[]}) # proportions non vulnerable: ages 2,3,4,5

    for i,line in enumerate(lines[j:]):
        row = line.strip().split()
        if len(row) != 4:
            break
        j += 1
        bse['fisheries'][i]['proportions_non_vulnerable'] = [float(s) for s in row]

    bse['natural_mortality_by_age'] = [float(s) for s in lines[j].split()]
    bse['incidental_mortality'] = [float(s) for s in lines[j+1].split()]
    bse['ocean_net_fisheries'] = [bool(int(s)) for s in lines[j+2].split()]
    j+=3

    for line in lines[j:]:
        row = line.strip().split()
        if not row[0].isdigit():
            break
        j+=1
        bse['terminal_fisheries'].append([bool(int(s)) for s in row])

    abbrevs = []
    for line in lines[j:]:
        match = stock_r.match(line.strip())
        bse['stocks'].append({
            'name': match.group(1), # Stock name
            'production_param': match.group(2), # Production parameter A Ricker A value for natural stocks Productivity for hatchery stocks
            'msy_esc_estimate': match.group(3), # Estimate of MSY escapement
            'idl': match.group(4), # IDLs for calibration runs only
            'hatchery_flag': bool(int(match.group(5))), # Flag for hatchery stocks
            'msh_esc_flag': bool(int(match.group(6))), # MSH escapement flag; true/1 truncates at maximum,  false/0 truncates at optimum
            'id': match.group(7), # stock abbreviation
            'age_conversion': match.group(8) # age 2 to 1 conversion factor
        })
        abbrevs.append(match.group(7))
    return (abbrevs,bse)

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
                "fishery_exploitation": []
            }
    return stocks

# this requires the order of the stock ids, from the .bse files
def write_stk(abbrevs,data,file):
    for sid in abbrevs:
        stock = data[sid]
        file.write(f"{sid}\n")
        for a in stock['cohort_abundance']:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for a in stock['maturation_rates']:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for a in stock['adult_equivalent']:
            file.write(f"{a:12.8E}  ")
        file.write("\n")

        for fishery in stock['fishery_exploitation']:
            for a in fishery:
                file.write(f"{a:12.8E}  ")
            file.write("\n")
