import re
import tempfile
import os

# TODO: document this
def parse_config(file):
    def cfg_row(l):
        return l.split(",")[0].strip()

    def y_or(l):
        r = cfg_row(l)
        return r[0] == "y" or r[0] == "Y" or r[0] == "1"

    lines = file.readlines()

    abd = 20 + int(cfg_row(lines[20]))  # amount of abundance indice lines
    end = abd + 17 + int(cfg_row(lines[abd + 17]))  # end of pnv files

    config = {
        "model_start_year": int(cfg_row(lines[1])),
        "sim_start_year": int(cfg_row(lines[end + 5])),
        "end_year": int(cfg_row(lines[2])),
        "calibration": y_or(lines[5]),
        "use_9525_evs": int(cfg_row(lines[7])),
        "minimum_terminal_age": int(cfg_row(lines[end + 2])),
        "additional_slcm": y_or(lines[end + 8]),
        "in_river": y_or(lines[end + 9]),
        "input": {
            "base": cfg_row(lines[3]),
            "stock": cfg_row(lines[4]),
            "maturation": cfg_row(lines[6]),
            "ev": cfg_row(lines[8]),
            "idl": {"enable": y_or(lines[9]), "file": cfg_row(lines[10])},
            "enh": cfg_row(lines[abd + 14]),
            "cnr": {
                "number": int(cfg_row(lines[abd + 15])),
                "file": cfg_row(lines[abd + 16]),
            },
            "pnv": {
                "changes": int(cfg_row(lines[abd + 17])),
                "files": [cfg_row(l) for l in lines[abd + 18 : end + 1]],
            },
            "fp": cfg_row(lines[end + 1]),
            "cei": {"enable": y_or(lines[end + 3]), "file": cfg_row(lines[end + 4])},
            "monte": {"enable": y_or(lines[end + 6]), "file": cfg_row(lines[end + 7])},
        },
        "output": {
            "enable": y_or(lines[11]),
            "prefix": cfg_row(lines[12]),
            "catch": y_or(lines[13]),
            "term_run": y_or(lines[14]),
            "escapement": y_or(lines[15]),
            "ocn": int(cfg_row(lines[16])),
            "exploitation": int(cfg_row(lines[17])),
            "mortalities": int(cfg_row(lines[18])),
            "incidental_mortality": y_or(lines[19]),
            "abundance": {
                "number": int(cfg_row(lines[20])),
                "fisheries": [int(cfg_row(s)) for s in lines[20:abd]],
            },
        },
        "report": {
            "header": cfg_row(lines[abd + 1]),
            "stock_prop": y_or(lines[abd + 2]),
            "rt": y_or(lines[abd + 3]),
            "catch": y_or(lines[abd + 4]),
            "stock_fishery": int(cfg_row(lines[abd + 5])),
            "shaker": y_or(lines[abd + 6]),
            "terminal_catch": y_or(lines[abd + 7]),
            "escapement": y_or(lines[abd + 8]),
            "harvest_rate": cfg_row(lines[abd + 9]),
            "compare_base_year": y_or(lines[abd + 10]),
            "document_model": y_or(lines[abd + 11]),
            "stocks_enhancement": int(cfg_row(lines[abd + 12])),
            "density_dependence": y_or(lines[abd + 13]),
        },
    }

    return config


def write_config(data, file):
    def upper_y(b):
        return "Y" if b else "N"

    def lower_y(b):
        return "y" if b else "n"

    def num_y(b):
        return 1 if b else 0

    file.write("Base case conditions\n")
    file.write(
        f"""
{data['model_start_year']}  ,  START YEAR FOR MODEL RUN
{data['end_year']}  ,  NUMBER OF YEARS FOR SIMULATION -1 year!!!!
{data['input']['base']} ,  BASE DATA FILE NAME
{data['input']['stock']} ,  STOCK DATA FILE
{upper_y(data['calibration'])} ,  MODEL CALIBRATION
{data['input']['maturation']} ,  MATURATION FILE
{data['use_9525_evs']} ,  USE EVS FROM CALIBRATION 9525
{data['input']['ev']}  ,     EV FILE NAME
{upper_y(data['input']['idl']['enable'])} ,  USE IDL FILE\n"""[
            1:
        ]
    )
    if data["input"]["idl"]["enable"]:
        file.write(f"{data['input']['idl']['file']}\n")

    file.write(
        f"""
{upper_y(data['output']['enable'])}  ,  SAVE STATISTICS IN DISK FILES?
{data['output']['prefix']} ,     PREFIX FOR SAVE FILES
{num_y(data['output']['catch'])} ,     CATCH STATISTICS  (1=YES)
{num_y(data['output']['term_run'])} ,     TERM RUN STATISTICS  (1=YES)
{num_y(data['output']['escapement'])} ,     ESCAPEMENT STATISTICS  (1=YES)
{data['output']['ocn']} ,     OCN EXPLOITATION RATE STATISTICS  (0=No;1=Total Mortality Method;2=Cohort Method)
{data['output']['exploitation']} ,     TOTAL EXPLOITATION RATE STATISTICS (0=No;1=Total Mortality Method;2=Cohort Method)
{num_y(data['output']['mortalities'])} ,     TOTAL MORTALITIES BY STOCK & FISHERY  (1=YES)
{num_y(data['output']['incidental_mortality'])} ,     INCIDENTAL MORTALITY STATISTICS (1=YES)
{data['output']['abundance']['number']} ,  ABUNDANCE INDICES (# fisheries;followed by fishery #'s)\n"""[
            1:
        ]
    )

    for f in data["output"]["abundance"]["fisheries"]:
        file.write(f"{f} , FISHERY INDEX \n")

    file.write(
        f"""
{data['report']['header']} ,  REPORT GENERATION INSTRUCTIONS
{lower_y(data['report']['stock_prop'])} ,     STOCK PROP (Y/N)
{lower_y(data['report']['rt'])} ,     RT (Y/N)
{lower_y(data['report']['catch'])} ,     CATCH (Y/N)
{data['report']['stock_fishery']} ,     STOCK/FISHERY (0=N;1=TOTAL;2=CATCH;3=TIM)
{lower_y(data['report']['shaker'])} ,     SHAKER (Y/N)
{lower_y(data['report']['terminal_catch'])} ,     TERMINAL CATCH (Y/N)
{lower_y(data['report']['escapement'])} ,     ESCAPEMENT (Y/N)
{data['report']['harvest_rate']} ,     HARVEST RATE (N=No; CO=Cohort Method; TM=Total Mortality Method)
{num_y(data['report']['compare_base_year'])} ,     COMPARE STATISTICS TO BASE YEAR (1=YES)
{lower_y(data['report']['document_model'])} ,     DOCUMENT MODEL SETUP (Y/N)
{data['report']['stocks_enhancement']} ,  NUMBER OF STOCKS WITH ENHANCEMENT\n"""[
            1:
        ]
    )

    if data["report"]["stocks_enhancement"] > 0:
        file.write(f"{num_y(data['report']['density_dependence'])}\n")
        file.write(f"{data['input']['enh']}\n")

    file.write(f"{data['input']['cnr']['number']}\n")
    if data["input"]["cnr"]["number"] > 0:
        file.write(f"{data['input']['cnr']['file']}\n")

    file.write(f"{data['input']['pnv']['changes']}\n")
    if data["input"]["pnv"]["changes"] > 0:
        for p in data["input"]["pnv"]["files"]:
            file.write(f"{p} ,     PNV FILE NAME \n")

    file.write(
        f"""
{data['input']['fp']}   ,  STOCK SPECIFIC FP FILE NAME
{data['minimum_terminal_age']} ,  MINIMUM AGE FOR TERMINAL RUN STATS (3=Adults; 2=Jacks)
{upper_y(data['input']['cei']['enable'])} ,  CEILING STRATEGIES\n"""[
            1:
        ]
    )
    if data["input"]["cei"]["enable"]:
        file.write(
            f"{data['input']['cei']['file']} ,     FILE NAME FOR CEILING STRATEGY - forced thru 94 only\n"
        )
    file.write(f"{data['sim_start_year']} ,  first simulation year\n")
    file.write(
        f"{upper_y(data['input']['monte']['enable'])} ,  monte configuration information?\n"
    )
    if data["input"]["monte"]["enable"]:
        file.write(f"{data['input']['monte']['file']}\n")
    file.write(f"{upper_y(data['additional_slcm'])}\n")
    file.write(f"N ,  in-river management\n")
