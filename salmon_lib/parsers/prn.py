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
            for i, rate in enumerate(row[1:]):
                years[year].append((cols[i], int(rate)))
    return years


def parse_prn(file):
    years = {}
    for line in file:
        row = line.split()
        year = int(row[0])
        years[year] = []
        for i, stlat in enumerate(row[1:]):
            years[year].append((i, int(stlat)))
    return years
