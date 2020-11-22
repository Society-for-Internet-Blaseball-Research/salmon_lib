import argparse
import struct

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Patch CRiSP map coordinate bounds.",
        epilog="Note: due to silly compiler optimizations, the longitude might be off by +/- 0.00005, "
        "but that's probably fine :)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        default="crisphv3.exe",
        metavar="INFILE",
        help="input CRiSP executable filename",
    )
    parser.add_argument(
        "-o",
        default="crisphv3_new.exe",
        metavar="OUTFILE",
        help="output CRiSP executable filename",
    )
    parser.add_argument(
        "--lat",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=argparse.SUPPRESS,
        help="latitude bounds",
        required=True,
    )
    parser.add_argument(
        "--lon",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=argparse.SUPPRESS,
        help="longitude bounds. Note that these are negated (degrees W)",
        required=True,
    )

    args = parser.parse_args()

    lat = args.lat
    lon = args.lon

    if lat[0] > lat[1]:
        lat[0], lat[1] = lat[1], lat[0]
    if lon[0] > lon[1]:
        lon[0], lon[1] = lon[1], lon[0]

    file_offset = 0x400C00

    with open(args.i, "rb") as f:
        s = bytearray(f.read())

    def ud(b):
        return struct.unpack("<d", b)[0]

    def pd(d):
        return struct.pack("<d", d)

    def get4(addr):
        return s[addr - file_offset : addr - file_offset + 4]

    def put4(addr, b):
        s[addr - file_offset : addr - file_offset + 4] = b

    old_lat_lo = ud(get4(0x41FA13) + get4(0x41FA2B))
    old_lat_hi = ud(get4(0x41FA1A) + get4(0x41FA32))
    old_lon_lo = ud(get4(0x41F9FB) + get4(0x41FA00))
    old_lon_hi = ud(get4(0x41F9FB) + get4(0x41FA24))
    print(
        f"old bounds (copy 1): lat=[{old_lat_lo}, {old_lat_hi}], lon=[{old_lon_lo}, {old_lon_hi}]"
    )

    old_lat_lo = ud(get4(0x41FA78) + get4(0x41FA90))
    old_lat_hi = ud(get4(0x41FA7F) + get4(0x41FA97))
    old_lon_lo = ud(get4(0x41F9FB) + get4(0x41FA00))
    old_lon_hi = ud(get4(0x41F9FB) + get4(0x41FA89))
    print(
        f"old bounds (copy 2): lat=[{old_lat_lo}, {old_lat_hi}], lon=[{old_lon_lo}, {old_lon_hi}]"
    )

    # don't touch 0x41f9fb: it's shared between lon_lo and lon_hi
    # fortunately, it's the least significant part of lon_lo and lon_hi

    lon_lo = pd(lon[0])
    put4(0x41FA00, lon_lo[4:])

    lon_hi = pd(lon[1])
    put4(0x41FA24, lon_hi[4:])
    put4(0x41FA89, lon_hi[4:])

    lat_lo = pd(lat[0])
    put4(0x41FA13, lat_lo[:4])
    put4(0x41FA2B, lat_lo[4:])
    put4(0x41FA78, lat_lo[:4])
    put4(0x41FA90, lat_lo[4:])

    lat_hi = pd(lat[1])
    put4(0x41FA1A, lat_hi[:4])
    put4(0x41FA32, lat_hi[4:])
    put4(0x41FA7F, lat_hi[:4])
    put4(0x41FA97, lat_hi[4:])

    new_lat_lo = ud(get4(0x41FA13) + get4(0x41FA2B))
    new_lat_hi = ud(get4(0x41FA1A) + get4(0x41FA32))
    new_lon_lo = ud(get4(0x41F9FB) + get4(0x41FA00))
    new_lon_hi = ud(get4(0x41F9FB) + get4(0x41FA24))
    print(
        f"new bounds (copy 1): lat=[{new_lat_lo}, {new_lat_hi}], lon=[{new_lon_lo}, {new_lon_hi}]"
    )

    new_lat_lo = ud(get4(0x41FA78) + get4(0x41FA90))
    new_lat_hi = ud(get4(0x41FA7F) + get4(0x41FA97))
    new_lon_lo = ud(get4(0x41F9FB) + get4(0x41FA00))
    new_lon_hi = ud(get4(0x41F9FB) + get4(0x41FA89))
    print(
        f"new bounds (copy 2): lat=[{new_lat_lo}, {new_lat_hi}], lon=[{new_lon_lo}, {new_lon_hi}]"
    )

    with open(args.o, "wb") as f:
        f.write(s)
