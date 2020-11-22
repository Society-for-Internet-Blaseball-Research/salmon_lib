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


def parse_msc(file):
    """
    format:
    {'maturation_file': 'input/hanford.mat',
     'stocks': [('AKS', 'Alaska Spring'),
            ('BON', 'Bonneville'),
            ('CWF', 'Cowlitz Fall'),
            ('GSH', 'Georgia Strait Hatchery'),
            ('LRW', 'Lewis River Wild'),
            ('ORC', 'Oregon Coastal'),
            ('RBH', 'Robertson Creek Hatchery'),
            ('RBT', 'WCVI Wild'),
            ('SPR', 'Spring Creek'),
            ('URB', 'Columbia River Upriver Bright'),
            ('WSH', 'Willamette Spring')]}
    """

    msc = {
        "maturation_file": next(file).split()[0],
        "stocks": []
    }

    for line in file:
        row = line.split(',')
        msc["stocks"].append((row[0],row[1].strip()))

    return msc

def write_msc(data,file):
    file.write(f"{data['maturation_file']} , Name of maturation data file\n")
    for stock in data['stocks']:
        file.write(f"{stock[0]},   {stock[1]}\n")

# proportions_non_vulnerable file.
# this replaces proportions in the .bse file
def parse_pnv(file):
    """
    {
        'fishery': 4,
        'first_year': 1984,
        'last_year': 2017,
        'ages': [
            [0.5779,0.5779...],
            [0.1795,0.1795...],
            [0.1795,0.1795...],
            [0.0807,0.0807...]
        ]
    }
    """
    pnv = {
        "fishery": int(next(file)),
        "first_year": int(next(file)),
        "last_year": int(next(file)),
        "ages": [] # 4 age rows; each collumn is the value for a year. ages go 2-5.
    }

    for line in file:
        row = line.split()
        try:
            pnv['ages'].append([float(year) for year in row])
        except ValueError:
            break

    return pnv

def write_pnv(data,f):
    f.write(f"{data['fishery']}\n")
    f.write(f"{data['first_year']}\n")
    f.write(f"{data['last_year']}\n")

    for age_row in data['ages']:
        for value in age_row:
            f.write(f"{value:6.4f}  ") # 6 digits (counting .) total floats; 4 decimal places
        f.write("\n")


"""
*.fp file format:
The *.fp files are used for detailed Fishery Policy (Harvest Rate) scalars that
alter the impact of a given fishery on the stocks on a year-by-year basis. The
format is to place all of the FP values in a block for a year. Each year has a
separate block. Within each block the 30 rows are for the 30 stocks and each of
the 25 columns is one of the fisheries. There are no other flags, values or
tokens in this file.

lord what kind of structure should this return though
just...just a three-dimensional array?
"""


def parse_fp(file):
    """parse .fp files. returns a 3D array (nested lists):
    year x fishery x stock.
    The original base.fp file, for instance, returns a 39x30x25 array."""
    slices = file.read().strip().replace('\r', '').split('\n\n')
    return [[[float(s) for s in line.split()] for line in slice.splitlines()]
            for slice in slices]
