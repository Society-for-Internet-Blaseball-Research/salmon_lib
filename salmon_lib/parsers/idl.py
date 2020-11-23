def parse_idl(file):
    idl = {"number_stocks": int(next(file)), "stocks": []}

    for line in file:
        idl["stocks"].append(
            {
                "id": line.strip(),
                "first_year": int(next(file)),
                "last_year": int(next(file)),
                "scalars": [float(s) for s in next(file).split(",")],
            }
        )

    return idl


def write_idl(data, file):
    file.write(f"{data['number_stocks']}\n")
    for stock in data["stocks"]:
        file.write(f"{stock['id']}\n")
        file.write(f"{stock['first_year']}\n")
        file.write(f"{stock['last_year']}\n")
        file.write(",".join([f"{s:5.3f}" for s in stock["scalars"]]) + "\n")
