#!/usr/bin/python3

import os,sys
import re,yaml
import naive_parser

def getCountryNames(hoi4path):
    countryNameYmlPath = hoi4path + "localisation/countries_mod_l_english.yml"
    if not os.path.exists(countryNameYmlPath):
        countryNameYmlPath = hoi4path + "localisation/countries_l_english.yml"

    ymlData = open(countryNameYmlPath).read()
    ymlData = "\n".join(ymlData.split("\n")[1:])[1:]

    ymlData = re.sub(r':[0-9]*',r':', ymlData)
    ymlData = re.sub(r'\n ',r'\n', ymlData)

    ymlData = ymlData.encode("ascii",errors="ignore")
    countryNames = yaml.load(ymlData)

#    if isinstance(countryNames, str):
#        # I have to do everything myself around here
#        countryNames = {}
#        for line in ymlData.split('\n'):
#            print(line)
#            tag = line.split(":")[0]
#            print(tag)
#            quotes = line.split("\"")
#            if len(quotes) == 2:
#                name = line.split("\"")[1]
#                print(name)
#                countryNames[tag] = name

    return countryNames

def getCityNames(hoi4path):
    countryNameYmlPath = hoi4path + "localisation/victory_points_l_english.yml"

    try:
        ymlData = open(countryNameYmlPath).read()
    except:
        data = open(countryNameYmlPath, 'rb').read()
        ymlData = data.decode("utf8", "ignore")


    ymlData = "\n".join(ymlData.split("\n")[1:])[1:]

    ymlData = re.sub(r':[0-9]*',r':', ymlData)
    ymlData = re.sub(r'\n ',r'\n', ymlData)

    ymlData = ymlData.encode("ascii",errors="ignore")
    cityNames = yaml.load(ymlData)

    return list(cityNames.values())
