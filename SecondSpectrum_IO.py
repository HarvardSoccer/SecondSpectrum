#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 16 07:54:00 2020

@author: laurieshaw
"""

import json
import pandas as pd
import numpy as np


def read_match_metadata(DATADIR,fname):
    '''
    read in second spectrum metadata file
    '''
    f = open(DATADIR+fname, "r")
    metadata = json.load(f)
    return metadata

def read_tracking_data(DATADIR,fname):
    '''
    read in second spectrum tracking data file and convert to pandas dataframe
    '''
    frames = []
    fpath = DATADIR + fname
    for line in open(fpath, 'r'):
        frames.append( json.loads(line) )
    frames = pd.DataFrame(frames)
    # use the frameIdx field as the dataframe index
    frames.set_index('frameIdx',drop=True)
    return frames

def flip_positions(frames,metadata):
    '''
    reverse the direction of play in second half so each team is always shooting in the same direction
    '''
    second_half_idx = frames.index[ frames.period==2][0]
    for idx,row in frames.loc[second_half_idx:].iterrows():
        for p in row.homePlayers:
            p['xyz'][0] *= -1
            p['xyz'][1] *= -1
        for p in row.awayPlayers:
            p['xyz'][0] *= -1
            p['xyz'][1] *= -1

def find_substitutions(frames,metadata,subsample=25):
    ''' 
    find the substitutions for either team. Helpful for formation analysis, 
    as formations can only be measured during match periods where there are no substitutions)
    '''
    for team in ['home','away']: # do home and then away team
        # find starting lineup
        players_on_field = frames.iloc[0].homePlayers if team=='home' else frames.iloc[0].awayPlayers
        players_on_field = set( [p['number'] for p in players_on_field] )
        for i,frame in frames.iloc[::subsample].iterrows():
            # iterate through frames and check players on field
            players = frame.homePlayers if team=='home' else frame.awayPlayers
            player_in_frame = set( [p['number'] for p in players] )
            if players_on_field != player_in_frame:
                minutes = np.floor(frame.gameClock/60.)
                seconds = frame.gameClock-minutes*60.
                print( '%s team substitution occured on %d min, %d seconds:' % (team,(frame.period-1)*45+minutes,seconds))
                print( '    players off: ',players_on_field - player_in_frame)
                print( '    players on : ', player_in_frame - players_on_field)
                players_on_field = player_in_frame
