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


"""
{
    'Fishery': [
        (year,stat)
    ]
}
"""


def parse_abd(file):
    fisheries = {}
    curr_fishery = ""
    for line in file:
        if '"' in line:
            curr_fishery = line.strip('"').strip()
            fisheries[curr_fishery] = []
        else:
            row = line.split()
            fisheries[curr_fishery] = (row[0], row[1])
    return fisheries


"""
(pre terminal rt,terminal rt)
pre terminal rt = [
    (year,[stats]),
    ...
]
terminal is the same thing
"""


def parse_rt(file):
    terminal = []
    pre_terminal = []
    next(file)
    for line in file:
        row = line.split()
        if not row[0].isdigit():
            terminal = [(tline.split()[0], tline.split()[1:]) for tline in file]
        else:
            pre_terminal.append((row[0], row[1:]))
    return (pre_terminal, terminal)


"""
    index: {
        year: stat
    }
"""


def parse_prn(file):
    stats = {}

    for line in file:
        row = line.split()
        year = int(row[0])

        if len(stats) == 0:
            for i in range(0, len(row) - 1):
                stats[i] = {}

        for i, stlat in enumerate(row[1:]):
            val = 0
            try:
                val = int(stlat)
            except ValueError:
                try:
                    val = float(stlat)
                except ValueError:
                    val = stlat  # wow this is cursed

            stats[i][year] = val

    return stats
