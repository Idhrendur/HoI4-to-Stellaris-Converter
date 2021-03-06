#!/usr/bin/python3

import sys,os
import math
import naive_parser
import getCountryNames
import properties
import yaml
import numpy
from enum import Enum

class Event:
    def __init__(self,eventType,*tags):
        self.eventType = eventType
        self.tags = tags

    def __str__(self):
        printstring = self.eventType + " "
        for tag in self.tags:
            printstring += tag + " "
        return printstring

    def __eq__(self,other):
        return self.eventType == other.eventType

    def __lt__(self,other):
        return self.eventType < other.eventType

class Empire:
    def __init__(self,nation):
        self.nation = nation
        self.tag = self.nation.tag
        self.score = self.nation.points
        self.population = self.nation.population
        self.industry = self.nation.industry
        self.government = self.nation.government
        self.ideology = self.nation.ideology
        self.climate = self.nation.climate
        self.nuclear = False
        self.colour = "Red"

        self.planetClass = "pc_arid"
        self.penalty = 0
        self.planetSize = 10
        self.planetPopulation = 1
        self.tileBlockers = 8

    def longTag(self):
        return self.tag + "_" + self.government

    def GoIntoSpace(self):
        if self.industry > 0.6:
            self.planetClass = "pc_continental"
        elif self.industry > 0.4:
            if self.climate in ["pc_arid","pc_desert","pc_savanna"]:
                self.planetClass = "pc_tropical"
            else:
                self.planetClass = "pc_ocean"
        else:
            self.planetClass = self.climate

        popweight = (self.population + self.population + self.industry) / 3.0
        indweight = (self.population + self.industry + self.industry) / 3.0
        self.planetSize = 10 + math.floor(10*popweight)
        self.planetPopulation = max(1,math.floor(8*self.population))
        self.tileBlockers = 10 - (9*math.floor(indweight))

        if self.score < 0.1:
            self.penalty = 4
        elif self.score < 0.2:
            self.penalty = 3
        elif self.score < 0.4:
            self.penalty = 2
        elif self.score < 0.6:
            self.penalty = 1

    def __str__(self):
        printstring = self.tag + ": "
        printstring += self.planetClass + ". "
        printstring += "Size {}, population {}, {} tile blockers. {}0% penalty.".format(self.planetSize,self.planetPopulation, self.tileBlockers, self.penalty)
        return(printstring)

class Universe:
    def __init__(self,savefile,hoi4path):
        self.savefile = savefile
        self.hoi4path = hoi4path
        with open("files/Events.yml") as stream:
            self.eventStrings = yaml.load(stream)

    def Load(self):
        parser = naive_parser.Parser(self.savefile, self.hoi4path)
        self.topNations = parser.getTopNations()
        self.smallNations = parser.getSmallNations()
        self.gini = parser.getGiniCoeff()
        self.totalScore = parser.getTotalScore()

        self.seed = int(naive_parser.drill(self.savefile,"game_unique_seed"))
        currentDate = naive_parser.drill(self.savefile,"date")
        currentDate = currentDate.replace('"','')
        self.currentDate = [int(n) for n in currentDate.split(".")]

        self.events = []
        climateChange = 0
        self.nuclearWar = 0
        self.earthOwnedBy = ""
        climateAuthority = ""
        self.earthType = "pc_continental"

        self.empires = []
        for nation in self.topNations:
            self.empires.append(Empire(nation))

        if len(self.empires) == 1:
            self.events.append(Event("Hegemon",self.empires[0].tag))
            self.earthOwnedBy = self.empires[0].tag
            climateAuthority = self.empires[0].tag
            
        elif self.empires[0].score / self.totalScore > 0.5: # largest nation has 50%

            if self.empires[1].score / self.empires[0].score > 0.5: # next largest is pretty big
                self.events.append(Event("ColdWar",self.empires[0].tag, self.empires[1].tag))
                self.events.append(Event("MinorNuclearWar",self.empires[0].tag,self.empires[1].tag))
                self.events.append(Event("MinorNuclearWarLose",self.empires[1].tag))
                self.events.append(Event("MinorNuclearWarWin",self.empires[0].tag))

                self.nuclearWar = 1
                self.earthOwnedBy = self.empires[0].tag
                self.empires[0].nuclear = True
                self.empires[1].nuclear = True
                self.empires[1].population *= 0.25

            else: # next largest is pretty small
                self.events.append(Event("EconomicCollapse",self.empires[1].tag))
                self.empires[1].industry *= 0.75
                self.events.append(Event("Hegemon",self.empires[0].tag))
                self.earthOwnedBy = self.empires[0].tag
                
        else: # largest nation does not have 50%

            if self.empires[0].score / self.totalScore > 0.3: # someone's large-ish
                if self.empires[1].score / self.empires[0].score > 0.5: # next largest is pretty big
                    if len(self.empires) == 2: # only two nations
                        self.events.append(Event("ColdWar",self.empires[0].tag, self.empires[1].tag))
                    elif (self.empires[2].score / self.empires[1].score > 0.5): # and next after that is pretty big too
                        self.events.append(Event("EconomicProblems",self.empires[2].tag))
                        self.empires[2].industry *= 0.9
                        self.events.append(Event("ColdWar",self.empires[0].tag, self.empires[1].tag))
                        self.events.append(Event("ColdWarStaysCold",self.empires[0].tag, self.empires[1].tag))
                        self.events.append(Event("Squabbling"))
                    else: # and next after that is pretty small
                        self.events.append(Event("EconomicCollapse",self.empires[2].tag))
                        self.empires[2].industry *= 0.75
                        self.events.append(Event("ColdWar",self.empires[0].tag, self.empires[1].tag))
                        if self.empires[0].government == self.empires[1].government and self.empires[0].government != "fascist":
                            self.events.append(Event("ColdWarStaysCold",self.empires[0].tag, self.empires[1].tag))
                            self.events.append(Event("Squabbling"))
                        else:
                            self.events.append(Event("NuclearWar",self.empires[0].tag, self.empires[1].tag))
                            self.nuclearWar = 2
                            self.events.append(Event("NuclearWarLose",self.empires[0].tag, self.empires[1].tag))
                            self.empires[0].nuclear = True
                            self.empires[1].nuclear = True
                            self.empires[0].population *= 0.25
                            self.empires[1].population *= 0.25

                else: # next largest is pretty small
                    self.events.append(Event("EconomicCollapse",self.empires[1].tag))
                    self.empires[1].industry *= 0.75
                    self.events.append(Event("Hegemon",self.empires[0].tag))
                    self.earthOwnedBy = self.empires[0].longTag()

            else: # everyone's tiny
                self.events.append(Event("Squabbling"))

        if self.gini > 0.4:
            if climateAuthority:
                self.events.append(Event("GovernmentClimateControl",climateAuthority))
            elif self.gini > 0.6:
                climateChange = 2
            else:
                climateChange = 1
        else:
            self.events.append(Event("CleanIndustrialization"))

        self.events.append(Event("Migrations"))

        if self.nuclearWar == 2:
            self.events.append(Event("TombWorld"))
            self.events.append(Event("EscapeLaunches"))
            self.earthType = "pc_nuked"
        elif self.nuclearWar == 1:
            if climateChange == 0:
                self.events.append(Event("NuclearWinter"))
                self.events.append(Event("EscapeLaunches"))
                self.earthType = "pc_arctic"
            elif climateChange == 1:
                self.events.append(Event("SeaLevelsRise"))
                self.events.append(Event("Launches"))
                self.earthType = "pc_ocean"
            elif climateChange == 2:
                self.events.append(Event("NuclearIndustrialDesert"))
                self.events.append(Event("EscapeLaunches"))
                self.earthType = "pc_desert"
        else:
            if climateChange == 0:
                self.earthType = "pc_continental"
                self.events.append(Event("Launches"))
                pass
            elif climateChange == 1:
                self.events.append(Event("SeaLevelsRise"))
                self.events.append(Event("Launches"))
                self.earthType = "pc_ocean"
            elif climateChange == 2:
                self.events.append(Event("GlobalWarming"))
                self.events.append(Event("EscapeLaunches"))
                self.earthType = "pc_arid"

        #for event in self.events:
        #    print(event)
    
        colourMap = properties.getColours(self.hoi4path)

        for empire in self.empires:

            if empire.tag in colourMap:
                empire.colour = colourMap[empire.tag]

            empire.GoIntoSpace()

        #for empire in self.empires:
        #    print(empire)

    def GetHistory(self):

        tagToName = {}
        tagToAdj = {}
        cityNames = ["Warsaw"]
        if self.hoi4path:
            cityNames = getCountryNames.getCityNames(self.hoi4path)
            countryNames = getCountryNames.getCountryNames(self.hoi4path)
            for empire in self.topNations+self.smallNations:
                name = countryNames[empire.longTag()+"_DEF"]
                name = name.replace("The","the")
                tagToName[empire.tag] = name
                adj = countryNames[empire.longTag()+"_ADJ"]
                tagToAdj[empire.tag] = adj

        numpy.random.seed(self.seed)

        startYear = self.currentDate[0] + 5
        endYear = 2200

        yearRange = endYear - startYear
        eventCount = numpy.random.randint(8,12)

        realEvents = []
        for event in self.events:
            if event.eventType in self.eventStrings:
                realEvents.append( Event(event.eventType, *event.tags) )

            if event.eventType+"0" in self.eventStrings:
                realEvents.append( Event(event.eventType+"0", *event.tags) )

            for i in range(1,10):
                #print(event.eventType+str(i))
                #print(event.eventType+str(i) in self.eventStrings)
                if event.eventType+str(i) in self.eventStrings and (numpy.random.random() < 0.7):
                    realEvents.append( Event(event.eventType+str(i), *event.tags) )
            

        randomEventCount = eventCount - len(realEvents)

        randomEventKeys = []
        for eventKey in sorted(self.eventStrings):
            if "Random" in eventKey:
                randomEventKeys.append(eventKey)

        randomEvents = []
        skips = 0
        while len(randomEvents) < randomEventCount:
            skips += 1
            if skips > 100: break
            chosenEvent = Event(numpy.random.choice(randomEventKeys))
            if chosenEvent not in randomEvents:
                randomEvents.append(chosenEvent)
        randomEvents.sort()

        if randomEventCount > 0:
            jump = eventCount // randomEventCount
            insertPoint = 2 - jump
            if jump == 1:
                insertPoint = 0
            for randomEvent in randomEvents:
                insertPoint += jump
                realEvents.insert(insertPoint, randomEvent)

        # Tried just having linear gaps between years; it doesn't feel right. We need a pretty dense cold-war 20th century and a pretty sparse 22nd century. Log scales to the rescue!
        logNudge = 80
        yearLogScale = numpy.logspace(numpy.log10(logNudge),numpy.log10(yearRange+logNudge), num=len(realEvents)+1)
        yearLogScale = [ x-logNudge for x in yearLogScale ]

        historyString = ""
        for e in range(len(realEvents)):
            year = int(numpy.floor(startYear + yearLogScale[e]))
            yearJump = (yearLogScale[e+1] - yearLogScale[e]) // 2
            if yearJump > 1:
                year += numpy.random.randint(-yearJump//2, yearJump//2)
            if year < startYear: year = startYear+1
            if year > endYear: year = endYear-1
            event = realEvents[e]
            print(event)

            replaces = {}
            replaces["&YEAR&"] = str(year)
            replaces["&DECADE&"] = str(year//10)+"0s"
            replaces["&NATION_1&"] = tagToName[event.tags[0]] if len(event.tags) > 0 else ""
            replaces["&NATION_2&"] = tagToName[event.tags[1]] if len(event.tags) > 1 else ""
            replaces["&NATION_1_ADJ&"] = tagToAdj[event.tags[0]] if len(event.tags) > 0 else ""
            replaces["&NATION_2_ADJ&"] = tagToAdj[event.tags[1]] if len(event.tags) > 1 else ""
            replaces["&RANDOM_SMALL_CITY&"] = numpy.random.choice(cityNames)
            replaces["&RANDOM_SMALL_NATION&"] = tagToName[numpy.random.choice(self.smallNations).tag]

            eventline = self.eventStrings[event.eventType]
            for replaceString in replaces:
                eventline = eventline.replace(replaceString, replaces[replaceString])
            historyString += eventline + "\n"

        historyString = historyString.replace(". the",". The")
        historyString = historyString.replace(": the",": The")

        print(historyString)
        return historyString

    def getEarthTypeFlag(self):
        if self.nuclearWar == 2:
            return "nuclear_war"
        elif self.earthOwnedBy:
            return "give_planet"
        else:
            return "un_bureaucracy"

    def getEarthOwner(self):
        return self.earthOwnedBy

    def getEarthClass(self):
        return self.earthType

    def getEmpires(self):
        return self.empires

if __name__ == "__main__":
    savefile = naive_parser.ParseSaveFile("postwar_1948_06_16_01.hoi4")

    universe = Universe(savefile,"D:/Steam/steamapps/common/Hearts of Iron IV/")
    universe.Load()

    for empire in universe.getEmpires():
        print(empire)
