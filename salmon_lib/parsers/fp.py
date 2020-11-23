"""
*.fp file format:
The *.fp files are used for detailed Fishery Policy (Harvest Rate) scalars that
alter the impact of a given fishery on the stocks on a year-by-year basis. The
format is to place all of the FP values in a block for a year. Each year has a
separate block. Within each block the 30 rows are for the 30 stocks and each of
the 25 columns is one of the fisheries. There are no other flags, values or
tokens in this file.

lord what kind of structure should this return though
just...just a three-dimensional array? That's what it's returning now!
This is a terrible format, probably. But that's ok, for now.
"""


def parse_fp(file):
    """parse .fp files. returns a 3D array (nested lists):
    year x stock x fishery.
    The original base.fp file, for instance, returns a 39x30x25 array."""
    slices = file.read().strip().replace("\r", "").split("\n\n")
    return [
        [[float(s) for s in line.split()] for line in slice.splitlines()]
        for slice in slices
    ]


def write_fp(data, f):
    """Write .fp files. Just takes a 3D array (nested list) and writes it.
    Each slice has an extra newline separating them."""
    for year in data:
        for fishery in year:
            f.write(" ")
            f.write(" ".join([f"{stock:10.8f}" for stock in fishery]))
            f.write("\n")
        f.write("\n")
