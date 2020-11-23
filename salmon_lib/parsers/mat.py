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
            stock = row[0].replace(",", "")
            years[curr_year][stock] = {
                2: (float(row[1]), float(row[2])),
                3: (float(row[3]), float(row[4])),
                4: (float(row[5]), float(row[6])),
            }
    return years


def write_mat(data, file):
    for yr, stocks in sorted(data.items()):
        file.write(f"{yr}\n")
        for name, stock in sorted(stocks.items()):
            file.write(
                f"      {name},     {stock[2][0]:6.4f}    {stock[2][1]:6.4f}    {stock[3][0]:6.4f}    {stock[3][1]:6.4f}    {stock[4][0]:6.4f}    {stock[4][1]:6.4f}\n"
            )


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

    msc = {"maturation_file": next(file).split()[0], "stocks": []}

    for line in file:
        row = line.split(",")
        msc["stocks"].append((row[0], row[1].strip()))

    return msc


def write_msc(data, file):
    file.write(f"{data['maturation_file']} , Name of maturation data file\n")
    for stock in data["stocks"]:
        file.write(f"{stock[0]},   {stock[1]}\n")
