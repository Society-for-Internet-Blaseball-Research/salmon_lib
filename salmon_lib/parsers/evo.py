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
        "start_year": int(lines[0].strip()),
        "end_year": int(lines[1].strip()),
        "stocks": [],
    }
    for line in lines[2:]:
        row = line.split()
        stock_id = int(row[0])
        evo["stocks"].append({"years": [], "log": []})
        for (i, scalar) in enumerate(row[1:]):
            if scalar == "Log":
                evo["stocks"][stock_id - 1]["log"] = row[i + 1 :]
                break
            else:
                evo["stocks"][stock_id - 1]["years"].append(float(scalar))
    return evo


def write_evo(data, file):
    file.write(f" {data['start_year']}\n")
    file.write(f" {data['end_year']}\n")
    for (i, stock) in enumerate(data["stocks"]):
        file.write(f"  {i+1} ")
        for year in stock["years"]:
            file.write(f"{year:E}  ")
        for thing in stock["log"]:
            file.write(f"{thing}  ")
        file.write("\n")
