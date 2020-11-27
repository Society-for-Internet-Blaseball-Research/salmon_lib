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
        "ages": [],  # 4 age rows; each column is value for a year. ages go 2-5
    }

    for line in file:
        row = line.split()
        try:
            pnv["ages"].append([float(year) for year in row])
        except ValueError:
            pnv["ages"].pop()  # remove empty last entry in list
            break

    return pnv


def write_pnv(data, f):
    f.write(f"{data['fishery']}\n")
    f.write(f"{data['first_year']}\n")
    f.write(f"{data['last_year']}\n")

    for age_row in data["ages"]:
        for value in age_row:
            f.write(
                f"{value:6.4f}  "
            )  # 6 digits (counting .) total floats; 4 decimal places
        f.write("\n")
