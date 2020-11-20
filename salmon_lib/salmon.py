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

def parse_config(file):
    def cfg_row(l):
        return l.split(',')[0].strip()
    def y_or(l):
        r = cfg_row(l)
        return (r[0] == "y" or r[0] == "Y" or r[0] == "1")

    lines = file.readlines()

    abd = 20+int(cfg_row(lines[20])) # amount of abundance indice lines
    end = abd+17+int(cfg_row(lines[abd+17])) # end of pnv files
    config = {
        'model_start_year': int(cfg_row(lines[1])),
        'sim_start_year': int(cfg_row(lines[end+5])),
        'end_year': int(cfg_row(lines[2])),
        'calibration': y_or(lines[5]),
        'use_9525_evs': int(cfg_row(lines[7])),
        'minimum_terminal_age': int(cfg_row(lines[end+2])),
        'additional_slcm': y_or(lines[end+8]),
        'in_river': y_or(lines[end+9]),
        'input': {
            'base': cfg_row(lines[3]),
            'stock': cfg_row(lines[4]),
            'maturation': cfg_row(lines[6]),
            'ev': cfg_row(lines[8]),
            'idl': {
                'enable': y_or(lines[9]),
                'file': cfg_row(lines[10])
            },
            'enh': cfg_row(lines[abd+14]),
            'cnr': {
                'number': int(cfg_row(lines[abd+15])),
                'file': cfg_row(lines[abd+16])
            },
            'pnv': {
                'changes': int(cfg_row(lines[abd+17])),
                'files': [cfg_row(l) for l in lines[abd+18:end+1]]
            },
            'fp': cfg_row(lines[end+1]),
            'cei': {
                'enable': y_or(lines[end+3]),
                'file': cfg_row(lines[end+4])
            },
            'monte': {
                'enable': y_or(lines[end+6]),
                'file': cfg_row(lines[end+7])
            }
        },
        'output': {
            'enable': y_or(lines[11]),
            'prefix': cfg_row(lines[12]),
            'catch': y_or(lines[13]),
            'term_run': y_or(lines[14]),
            'escapement': y_or(lines[15]),
            'ocn': int(cfg_row(lines[16])),
            'exploitation': int(cfg_row(lines[17])),
            'mortalities': int(cfg_row(lines[18])),
            'incidental_mortality': y_or(lines[19]),
            'abundance': {
                'number': int(cfg_row(lines[20])),
                'fisheries': [int(cfg_row(s)) for s in lines[20:abd]]
            }
        },
        'report': {
            'header': cfg_row(lines[abd+1]),
            'stock_prop': y_or(lines[abd+2]),
            'rt': y_or(lines[abd+3]),
            'catch': y_or(lines[abd+4]),
            'stock_fishery': int(cfg_row(lines[abd+5])),
            'shaker': y_or(lines[abd+6]),
            'terminal_catch': y_or(lines[abd+7]),
            'escapement': y_or(lines[abd+8]),
            'harvest_rate': cfg_row(lines[abd+9]),
            'compare_base_year': y_or(lines[abd+10]),
            'document_model': y_or(lines[abd+11]),
            'stocks_enhancement': int(cfg_row(lines[abd+12])),
            'density_dependence': y_or(lines[abd+13])
        }
    }

    return config

def write_config(data,file):
    def upper_y(b):
        return ('Y' if b else 'N')
    def lower_y(b):
        return ('y' if b else 'n')
    def num_y(b):
        return(1 if b else 0)

    file.write("Base case conditions\n")
    file.write(
    f"""
{data['model_start_year']}  ,  START YEAR FOR MODEL RUN
{data['end_year']}  ,  NUMBER OF YEARS FOR SIMULATION -1 year!!!!
{data['input']['base']} ,  BASE DATA FILE NAME
{data['input']['stock']} ,  STOCK DATA FILE
{upper_y(data['calibration'])} ,  MODEL CALIBRATION
{data['input']['maturation']} ,  MATURATION FILE
{data['use_9525_evs']} ,  USE EVS FROM CALIBRATION 9525
{data['input']['ev']}  ,     EV FILE NAME
{upper_y(data['input']['idl']['enable'])} ,  USE IDL FILE
{data['input']['idl']['file']} ,     FILE NAME FOR IDL
{upper_y(data['output']['enable'])}  ,  SAVE STATISTICS IN DISK FILES?
{data['output']['prefix']} ,     PREFIX FOR SAVE FILES
{num_y(data['output']['catch'])} ,     CATCH STATISTICS  (1=YES)
{num_y(data['output']['term_run'])} ,     TERM RUN STATISTICS  (1=YES)
{num_y(data['output']['escapement'])} ,     ESCAPEMENT STATISTICS  (1=YES)
{data['output']['ocn']} ,     OCN EXPLOITATION RATE STATISTICS  (0=No;1=Total Mortality Method;2=Cohort Method)
{data['output']['exploitation']} ,     TOTAL EXPLOITATION RATE STATISTICS (0=No;1=Total Mortality Method;2=Cohort Method)
{num_y(data['output']['mortalities'])} ,     TOTAL MORTALITIES BY STOCK & FISHERY  (1=YES)
{num_y(data['output']['incidental_mortality'])} ,     INCIDENTAL MORTALITY STATISTICS (1=YES)
{data['output']['abundance']['number']} ,  ABUNDANCE INDICES (# fisheries;followed by fishery #'s)"""[1:])

    for f in data['output']['abundance']['fisheries']:
        file.write(f"{f} , FISHERY INDEX \n")

    file.write(
    f"""
{data['report']['header']} ,  REPORT GENERATION INSTRUCTIONS
{lower_y(data['report']['stock_prop'])} ,     STOCK PROP (Y/N)
{lower_y(data['report']['rt'])} ,     RT (Y/N)
{lower_y(data['report']['catch'])} ,     CATCH (Y/N)
{data['report']['stock_fishery']} ,     STOCK/FISHERY (0=N;1=TOTAL;2=CATCH;3=TIM)
{lower_y(data['report']['shaker'])} ,     SHAKER (Y/N)
{lower_y(data['report']['terminal_catch'])} ,     TERMINAL CATCH (Y/N)
{lower_y(data['report']['escapement'])} ,     ESCAPEMENT (Y/N)
{data['report']['harvest_rate']} ,     HARVEST RATE (N=No; CO=Cohort Method; TM=Total Mortality Method)
{num_y(data['report']['compare_base_year'])} ,     COMPARE STATISTICS TO BASE YEAR (1=YES)
{lower_y(data['report']['document_model'])} ,     DOCUMENT MODEL SETUP (Y/N)
{data['report']['stocks_enhancement']} ,  NUMBER OF STOCKS WITH ENHANCEMENT
{num_y(data['report']['density_dependence'])} ,     Density Dependence (1=On)
{data['input']['enh']} ,     FILE FOR ENHANCEMENT SPECS
{data['input']['cnr']['number']} ,  NUMBER OF CNR FISHERIES
{data['input']['cnr']['file']} ,     FILE NAME FOR CNR FISHERIES
{data['input']['pnv']['changes']} ,  NUMBER OF PNV CHANGES\n""")

    for p in data['input']['pnv']['files']:
        file.write(f"{p} ,     PNV FILE NAME \n")

    file.write(
    f"""
{data['input']['fp']}   ,  STOCK SPECIFIC FP FILE NAME
{data['minimum_terminal_age']} ,  MINIMUM AGE FOR TERMINAL RUN STATS (3=Adults; 2=Jacks)
{upper_y(data['input']['cei']['enable'])} ,  CEILING STRATEGIES
{data['input']['cei']['file']} ,     FILE NAME FOR CEILING STRATEGY - forced thru 94 only
{data['sim_start_year']} ,  first simulation year
{upper_y(data['input']['monte']['enable'])} ,  monte configuration information?
{data['input']['monte']['file']}
{upper_y(data['additional_slcm'])} ,  additional save stats for slcm?
{upper_y(data['in_river'])} ,  in-river management"""[1:])
