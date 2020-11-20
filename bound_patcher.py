import struct

# change these: these are coordinate ranges
# note that longitude is negated
# due to silly compiler optimizations, the longitude might be off by +/- 0.00005, but that's probably fine :)
lat = [42.33, 60.2]
lon = [104.1, 140.2]

assert lat[0] < lat[1]
assert lon[0] < lon[1]

file_offset = 0x400c00

with open("crisphv3.exe","rb") as f:
    s = bytearray(f.read())

def ud(b):
    return struct.unpack('<d', b)[0]

def pd(d):
    return struct.pack('<d', d)

def get4(addr):
    return s[addr-file_offset:addr-file_offset+4]

def put4(addr, b):
    s[addr-file_offset:addr-file_offset+4] = b

old_lon_lo = ud(get4(0x41f9fb) + get4(0x41fa00))
old_lon_hi = ud(get4(0x41f9fb) + get4(0x41fa24))
old_lat_lo = ud(get4(0x41fa13) + get4(0x41fa2b))
old_lat_hi = ud(get4(0x41fa1a) + get4(0x41fa32))
print("old lon (copy 1): [{}, {}]".format(old_lon_lo, old_lon_hi))
print("old lat (copy 1): [{}, {}]".format(old_lat_lo, old_lat_hi))

old_lon_lo = ud(get4(0x41f9fb) + get4(0x41fa00))
old_lon_hi = ud(get4(0x41f9fb) + get4(0x41fa89))
old_lat_lo = ud(get4(0x41fa78) + get4(0x41fa90))
old_lat_hi = ud(get4(0x41fa7f) + get4(0x41fa97))
print("old lon (copy 2): [{}, {}]".format(old_lon_lo, old_lon_hi))
print("old lat (copy 2): [{}, {}]".format(old_lat_lo, old_lat_hi))

# don't touch 0x41f9fb: it's shared between lon_lo and lon_hi

lon_lo = pd(lon[0])
put4(0x41fa00, lon_lo[4:])

lon_hi = pd(lon[1])
put4(0x41fa24, lon_hi[4:])
put4(0x41fa89, lon_hi[4:])

lat_lo = pd(lat[0])
put4(0x41fa13, lat_lo[:4])
put4(0x41fa2b, lat_lo[4:])
put4(0x41fa78, lat_lo[:4])
put4(0x41fa90, lat_lo[4:])

lat_hi = pd(lat[1])
put4(0x41fa1a, lat_hi[:4])
put4(0x41fa32, lat_hi[4:])
put4(0x41fa7f, lat_hi[:4])
put4(0x41fa97, lat_hi[4:])

new_lon_lo = ud(get4(0x41f9fb) + get4(0x41fa00))
new_lon_hi = ud(get4(0x41f9fb) + get4(0x41fa24))
new_lat_lo = ud(get4(0x41fa13) + get4(0x41fa2b))
new_lat_hi = ud(get4(0x41fa1a) + get4(0x41fa32))
print("new lon (copy 1): [{}, {}]".format(new_lon_lo, new_lon_hi))
print("new lat (copy 1): [{}, {}]".format(new_lat_lo, new_lat_hi))

new_lon_lo = ud(get4(0x41f9fb) + get4(0x41fa00))
new_lon_hi = ud(get4(0x41f9fb) + get4(0x41fa89))
new_lat_lo = ud(get4(0x41fa78) + get4(0x41fa90))
new_lat_hi = ud(get4(0x41fa7f) + get4(0x41fa97))
print("new lon (copy 2): [{}, {}]".format(new_lon_lo, new_lon_hi))
print("new lat (copy 2): [{}, {}]".format(new_lat_lo, new_lat_hi))

with open("crisphv3_new.exe","wb") as f:
    f.write(s)
