def parse_enh(file):
    enh = {"first_year": int(next(file)), "last_year": int(next(file)), "stocks": []}

    for line in file:
        row = line.split()
        years = next(file).split()
        enh["stocks"].append(
            {
                "id": int(row[0]),
                "productivity_param": float(row[1]),
                "smolt_rate": float(row[2]),
                "broodstock_spawner_proportion": float(row[3]),
                "changes": [int(year) for year in years],
            }
        )

    return enh


"""
  1979
  2017
     5   4.544    0.0715        1
     0        0        0  2877594
"""


def write_enh(data, file):
    file.write(f"  {data['first_year']}\n")
    file.write(f"  {data['last_year']}\n")

    for stock in data["stocks"]:
        file.write(f"     {stock['id']}")
        file.write(f"   {stock['productivity_param']:5.3f}")
        file.write(f"    {stock['smolt_rate']:6.4f}")
        file.write(f"        {stock['broodstock_spawner_proportion']:3.1f}")
        file.write("\n")
        for year in stock["changes"]:
            file.write(f"        {year}")
        file.write("\n")
