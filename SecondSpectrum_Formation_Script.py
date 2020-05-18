#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 20:30:36 2020

@author: laurieshaw
"""

import SecondSpectrum_IO as ssio
import SecondSpectrum_Formations as ssform

DATADIR = '/Users/laurieshaw/Documents/Football/Data/TrackingData/SecondSpectrum/Leicester/Mladen/'
fname_metadata = 'g1059881_SecondSpectrum_Metadata.json'
fname_trackingdata = 'g1059881_SecondSpectrum_Data.jsonl'

# load data
print("Loading data")
metadata = ssio.read_match_metadata(DATADIR, fname_metadata)
frames = ssio.read_tracking_data(DATADIR,fname_trackingdata)

# reverse the direction of play in second half so each team is always shooting in the same direction
ssio.flip_positions(frames,metadata)

# find timing of substitutions. Formations can only be measured when the same 10 outfield players are on the field
# so need to measure them seperately before and after.
print("Finding substitutions")
ssio.find_substitutions(frames,metadata,subsample=25)

''' above line should print the following:
    
home team substitution occured on 68 min, 10 seconds:
    players off:  {10}
    players on :  {18}
away team substitution occured on 68 min, 49 seconds:
    players off:  {27}
    players on :  {3}
away team substitution occured on 76 min, 58 seconds:
    players off:  {66}
    players on :  {8}
away team substitution occured on 84 min, 58 seconds:
    players off:  {15}
    players on :  {48}
'''

# based on this measure formation for home team from 0-68th minute and 69th-end
# first do 0-68th minute
print("Measuring home team formations")
start_period = (1,0) # start of first half
end_period = (2,23) # 23rd minute of second half (68th minute)
home_attack,home_defence = ssform.calc_formations_during_period('home',frames,metadata,start_period,end_period,gk_number=[1])
# plot formations
home_attack.plot_formation(metadata,title='West Ham (attacking): 0-68th minute')
home_defence.plot_formation(metadata,title='West Ham (defending): 0-68th minute')
# first do 69th-match end 
start_period = (2,69-45) # start of first half
end_period = (2,50) # can just set match end minute to some arbitrary high number
home_attack,home_defence = ssform.calc_formations_during_period('home',frames,metadata,start_period,end_period,gk_number=[1])
# plot formations
home_attack.plot_formation(metadata,title='West Ham (attacking): 69th+ minute')
home_defence.plot_formation(metadata,title='West Ham (defending): 69th+ minute')

# Liverpool (away team) make frequent substitutions after the 68th minute, so just measure formation to the first substitution
# 0-68th minute
print("Measuring away team formations")
start_period = (1,0) # start of first half
end_period = (2,23) # 23rd minute of second half (68th minute)
home_attack,home_defence = ssform.calc_formations_during_period('away',frames,metadata,start_period,end_period,gk_number=[1])
# plot formations
home_attack.plot_formation(metadata,title='Liverpool (attacking): 0-68th minute')
home_defence.plot_formation(metadata,title='Liverpool (defending): 0-68th minute')
