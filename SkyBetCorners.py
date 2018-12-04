# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 11:49:05 2018

@author: tom_m
"""

from urllib.request import Request as Request
from urllib.request import urlopen as urlopen;
from bs4 import BeautifulSoup as soup;
from datetime import datetime
import math
import re
import csv
import os

def mappingGet() :
    with open('mappingSkyTotalCorner.csv', 'r') as fileread :
        reader = csv.reader(fileread)
        mappingList = list(reader)
        fileread.close()
        
        # Convert it into a dict
        mapping = {}
        for item in mappingList :
            mapping[item[0]] = item[1]
            
        return mapping

def mappingSave(mapping) :
    # Convert it from a dict back to a list
    mappingList = []
    keys = sorted(mapping.keys())
    
    for key in keys :
        mappingList.append([key, mapping[key]])
    
    with open("mappingSkyTotalCorner.csv", "w", newline='') as filewrite :
        writer = csv.writer(filewrite)
        writer.writerows(mappingList)
        filewrite.close()
        
def mappingUpdate(competitor, mapping) :
    if competitor not in mapping :
        print('{} does not exist in mapping'.format(competitor))
        print('Enter team number from TotalCorner.com: ')
        pageNum = input()
        print('{} mapped to {} in TotalCorner\n'.format(competitor, pageNum))
        mapping[competitor] = pageNum
        
        return True
    else :
        return False
        
def TC_getCornerData(url) :
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.107 Safari/537.36','Upgrade-Insecure-Requests': '1','x-runtime': '148ms'};

    req = Request(url, headers = headers);
    TC_page = urlopen(req);
    TC_page_html = TC_page.read();
    TC_page.close();
    TC_page_soup = soup(TC_page_html, "html.parser");
    
    titleDiv = TC_page_soup.findAll("div", {"id":"team_view_title"})
    titleText = titleDiv[0].div.h4.contents[0]
    
    regexMatch = re.compile('([\S\s]+) - ([\S\s]+)').match(titleText)
    competitorName = regexMatch.group(1)
    
    table = TC_page_soup.findAll("table", {"id":"inplay_match_table"})[0]
    tablebody = table.findAll("tbody", {"class":"tbody_match"})[0]
    tablerows = tablebody.findAll("tr")
    
    results = []
    
    for matchIndex in range(0,len(tablerows)) :
        tr = tablerows[matchIndex]
        
        # Get the match status
        matchStatus = tr.find("span", {"class" : "match_status_minutes"}).contents
        if len(matchStatus) == 0 :
            continue;
        elif matchStatus[0] != 'Full' :
            continue;
        
        # Get match corners
        matchCornersFT = tr.find("span", {"class" : "span_match_corner"}).contents[0]
        matchCornersHT = tr.find("span", {"class" : "span_half_corner"}).contents[0]
        
        HT_regexMatch = re.compile('\(([\d]+)[\s]*-[\s]*([\d]+)\)').match(matchCornersHT)
        H1T_Home = int(HT_regexMatch.group(1))
        H1T_Away = int(HT_regexMatch.group(2))
        
        FT_regexMatch = re.compile('([\d]+)[\s]*-[\s]*([\d]+)').match(matchCornersFT)
        H2T_Home = int(FT_regexMatch.group(1)) - H1T_Home
        H2T_Away = int(FT_regexMatch.group(2)) - H1T_Away
        
        H1T_Total = H1T_Home + H1T_Away
        H2T_Total = H2T_Home + H2T_Away
        
        results.append([H1T_Total, H2T_Total])
        
    return {"competitorName": competitorName, "data": results}

def getWeightings() :
    with open('weightings.csv', 'r') as fileread :
        reader = csv.reader(fileread)
        weightingsList = list(reader)
        fileread.close()
        weightings = []
        for weight in weightingsList :
            weightings.append(float(weight[0]))
        normalisation = sum(weightings)
        for i in range(0,len(weightings)) :
            weightings[i] = weightings[i]/normalisation
    return weightings

def getWeightedProbability(weightings, data) :
    success = {
        "probability" : 0,
        "history": [],
        "odds" : math.inf
    }
    
    if len(data) < len(weightings) :
        # Adjust weightings to fit length of data
        length = len(data)
        newTotal = sum(weightings[0:length])
        newWeightings = []
        for index in range(0,length) :
            newWeightings.append(weightings[index]/newTotal)
            
        weightings = newWeightings
    
    for matchIndex in range(0, len(data)) :
        
        # Determine if the bet was successful
        match = data[matchIndex]
        matchResult = 0
        
        if (match[0] >= 3 and match[1] >= 3) :
            matchResult = 1
        
        success['history'].append(matchResult)
        success['probability'] += weightings[matchIndex]*matchResult
        
        if matchIndex >= len(weightings)-1 :
            break
        
    success["odds"] = 1/success['probability']
    
    return success

def saveResults(summary, title) :
    
    regexDate = re.compile('[\w]+ ([\d]+)[\w]+ ([\w]+) ([\d]+)').match(title)
    day = int(regexDate.group(1))
    month = regexDate.group(2)
    year = int(regexDate.group(3))
    datetime_object = datetime.strptime('{:02} {} {}'.format(day,month,year), '%d %B %Y')
    filename = datetime_object.strftime("%Y%m%d")
    
    output = [['goodBet', 'betStrength', 'oddsCalculated', 'oddsSkyBet', 'time', 'title']]
    for match in summary :
        output.append([match['goodBet'], match['betStrength'], match['oddsCalculated'], match['oddsSkyBet'], match['time'], match['title']])
    
    filepath = "records/{}.csv".format(filename)
    if not os.path.isfile(filepath) :
        with open(filepath, "w", newline='') as filewrite :
            writer = csv.writer(filewrite)
            writer.writerows(output)
            filewrite.close()
    else :
        print('\nOutput file already exists.')
        
def unique(list1): 
    unique_list = [] 
    for x in list1: 
        if x not in unique_list: 
            unique_list.append(x)
    return unique_list

headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.107 Safari/537.36','Upgrade-Insecure-Requests': '1','x-runtime': '148ms'};
pageURL = "https://m.skybet.com/football/coupon/10011490"

totalcornerBaseURL = "https://www.totalcorner.com/team/view/"

accordionNumbersAccepted = [1]

# Opening connection, grabbing the page
req = Request(pageURL, headers = headers);
page = urlopen(req);
page_html = page.read();
page.close();

page_soup = soup(page_html, "html.parser");

accordions = page_soup.findAll("li", {"class":"accordion--generic js-toggle"});

mapping = mappingGet()
weightings = getWeightings()
summary = []

for accordionNumber in range(0,len(accordions)) :
    if accordionNumber not in accordionNumbersAccepted :
        continue
    
    accordion = accordions[accordionNumber]
    accordionTitle = accordion.h2.span.contents[0]
    
    title = accordion.h2.span.contents[0]
    
    print('Processing {}...\n'.format(title))

    tablerows = accordion.table.tbody.findAll("tr")
    
    # Loop through the table rows once initially to check mapping
    for tr in tablerows :
        if (tr.td.attrs['class'][0] == 'group-header') :
            continue
        tds = tr.findAll("td")
        competitorsText = tds[0].a.b.contents[0]
        regex = re.compile('([\S\s]+) v ([\S\s]+)')
        regexMatch = regex.match(competitorsText)
        competitor1 = regexMatch.group(1)
        competitor2 = regexMatch.group(2)
        print('{} vs {}'.format(competitor1, competitor2))
        
        # Check the teams exist in the mapping
        update1 = mappingUpdate(competitor1, mapping)
        update2 = mappingUpdate(competitor2, mapping)
        if update1 or update2 :
            mappingSave(mapping)
    
    print(''.format())
    
    # Loop through the table rows
    time = '00:00'
    times = []
    strengths = []
    for tr in tablerows :
        if (tr.td.attrs['class'][0] == 'group-header') :
            headerText = tr.td.contents[0]
            KO_regex = re.compile('([\d]{2}:[\d]{2})').search(headerText)
            time = KO_regex.group(1)
            times.append(time)
            continue
        tds = tr.findAll("td")
        competitorsText = tds[0].a.b.contents[0]
        
        regex = re.compile('([\S\s]+) v ([\S\s]+)')
        regexMatch = regex.match(competitorsText)
        competitor1 = regexMatch.group(1)
        competitor2 = regexMatch.group(2)
        print('{} vs {}'.format(competitor1, competitor2))
        
        oddsText = tds[1].find("span", {"class":"js-oc-price js-not-in-slip"}).contents[0]
        regexOddsMatch = re.compile('([\d]+)\/([\d]+)').search(oddsText)
        odds = float(regexOddsMatch.group(1))/float(regexOddsMatch.group(2)) + 1
        
        competitor1_TC_url = '{}{}'.format(totalcornerBaseURL, mapping[competitor1])
        competitor2_TC_url = '{}{}'.format(totalcornerBaseURL, mapping[competitor2])
        
        # Grab totalcorner data
        results1 = TC_getCornerData(competitor1_TC_url)
        results2 = TC_getCornerData(competitor2_TC_url)
        
        success1 = getWeightedProbability(weightings, results1['data'])
        success2 = getWeightedProbability(weightings, results2['data'])
        oddsMean = (success1['odds'] + success2['odds'])/2
        
        goodBet = oddsMean < odds
        betStrength = odds/oddsMean
        
        strengths.append(betStrength)
        
        matchSummary = {
                'title': '{} vs {}'.format(competitor1, competitor2),
                'oddsCalculated' : oddsMean,
                'oddsSkyBet' : odds,
                'goodBet' : goodBet,
                'betStrength' : betStrength,
                'time': time}
        
        print('TC: {} | Eq Odds: {:.3f} | History: {}'.format(results1['competitorName'], success1['odds'], success1['history']))
        print('TC: {} | Eq Odds: {:.3f} | History: {}'.format(results2['competitorName'], success2['odds'], success2['history']))
        print(' {:>1} | Strength: {:>4.3f} | Calc: {:.3f} | SkyBet: {:.2f} | {} | {}'.format(matchSummary['goodBet'], matchSummary['betStrength'], matchSummary['oddsCalculated'], matchSummary['oddsSkyBet'], matchSummary['time'], matchSummary['title']))
        
        summary.append(matchSummary)
        
        print(''.format())
        

    print('Full Summary')
    for match in summary :
        print(' {:>1} | Strength: {:>4.3f} | Calc: {:.3f} | SkyBet: {:.2f} | {} | {}'.format(match['goodBet'], match['betStrength'], match['oddsCalculated'], match['oddsSkyBet'], match['time'], match['title']))
    
    print('')
    print('Chronological Summary')
    timesUniqueSorted = unique(sorted(times))
    strengthsUniqueSorted = unique(sorted(strengths, reverse=True))
    for time in timesUniqueSorted :
        for strength in strengthsUniqueSorted :
            for match in summary :
                if match['goodBet'] and match['time'] == time and match['betStrength'] == strength :
                    print(' {:>1} | Strength: {:>4.3f} | Calc: {:.3f} | SkyBet: {:.2f} | {} | {}'.format(match['goodBet'], match['betStrength'], match['oddsCalculated'], match['oddsSkyBet'], match['time'], match['title']))
    
    # Save results
    saveResults(summary, title)











