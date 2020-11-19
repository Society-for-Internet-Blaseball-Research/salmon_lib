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
