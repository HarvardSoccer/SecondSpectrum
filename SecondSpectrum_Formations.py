# -*- coding: utf-8 -*-
"""
Created on Thu May  2 16:06:44 2019

@author: laurieshaw
"""

import SecondSpectrum_Viz as viz
import numpy as np

def calc_formations_during_period(team,frames,metadata,period_start,period_end,gk_number=[1],min_possession_length_secs=5, subsample=5):
    ''' 
    calculates a team's attacking (in possession) and defensive (out of possession) formations during a specified period of the match. 
    
    For example, if min_possession_length_secs=5 seconds, possessions that lasted less than 5 seconds will not be used.

    The algorithm operates as follows:
        * find possessions for either team during the specified period, each of which must be at least min_possession_length_secs in length)
        * measure the structure ('lattice') of the team at each instant duration these possessions
        * aggregate together the lattices over all possessions to measure average offensive & defensive formations over the period
            
    Formation analysis can't handle personnel changes, so formations must be measured seperately before and after substitutions

    Based on methodology described in paper published here: https://static.capabiliaserver.com/frontend/clients/barca/wp_prod/wp-content/uploads/2020/01/56ce723e-barca-conference-paper-laurie-shaw.pdf
    
    Parameters
    -----------
    
    team: string dictating which team to calculate formations for. Set to either 'home' or 'away'
    frames: tracking data dataframe
    metadata: second spectrum metadata
    period_start: tuple of (half,minute) specifying the time at which we start to measure formations. e.g. period_start=(2,15) would be from the 60th minute
    period_end: tuple of (half,minute) specifying the time at which we stop measuring formations. e.g. period_end=(2,45) would be from the 90th minute
    gk_number: list of jersey numbers for goalkeepers in the team. Normally this would be a length one list, but can be longer if a team changed goalkeeper
    min_possession_length_secs: minimum length of a single possession of the ball (in seconds) to be included in formation measures
    subsample: Subsample frames so that we are not using every frame.
    
    Returns
    ---------
    attack_formation: formation object that holds the attacking formation of the team, measured during the specified period
    defence_formation: formation object that holds the defensive formation of the team, measured during the specified period
    
    
    '''
    # start and end indices of period within which to calcualte formations
    start_idx = frames.index[ (frames.period==period_start[0]) & (frames.gameClock>=period_start[1]*60.0)][0]
    end_idx = frames.index[ (frames.period==period_end[0]) & (frames.gameClock<=period_end[1]*60.0)][-1]
    # extract frames. End the period early if the team makes a substitution
    frames = frames.loc[start_idx:end_idx]
    frames = frames.loc[:index_of_substitution(team,frames)]
    # not find periods of possession lasting the specified time
    min_possession_length_frames = int( min_possession_length_secs*metadata['fps'] )
    # find the start and end frames of each period in possession of the ball
    team_possessions_start, team_possessions_end = get_team_possession_frames(team,frames.lastTouch,frames.live,min_possession_length_frames)
    print(len(team_possessions_start))
    # calculate the attacking formations, measured over all the individual possessions
    attack_formation = formation(team+'_attack',gk_number) # initialise formation object
    for pstart,pend in zip(team_possessions_start,team_possessions_end):
        for i,frame in frames.iloc[pstart:pend:subsample].iterrows():
            players = frame.homePlayers if team=='home' else frame.awayPlayers
            attack_formation.add_latice( lattice(players,gk_number,frame.gameClock)  ) # measure formations in individual frames
    attack_formation.calc_average_lattice(metadata) # average together formations over frames
    # now want to find all periods of possession for the opponents 
    opp = 'away' if team=='home' else 'home'
    # find the start and end frames of each period in which the opponents are in possession of the ball
    opp_possessions_start, opp_possessions_end = get_team_possession_frames(opp,frames.lastTouch,frames.live,min_possession_length_frames)
    # calculate the defensive formations, measured over all the individual possessions
    defence_formation = formation(team+'_defence',gk_number)
    for pstart,pend in zip(opp_possessions_start,opp_possessions_end):
        for i,frame in frames.iloc[pstart:pend:subsample].iterrows():
            players = frame.homePlayers if team=='home' else frame.awayPlayers
            defence_formation.add_latice(lattice(players,gk_number,frame.gameClock)  )
    defence_formation.calc_average_lattice(metadata) # average together formations over frames
    return attack_formation,defence_formation

def get_team_possession_frames(team,lastTouch,live,min_possession_length_frames):
    # finds the start and end frames of each of the individual possessions for a team that last at least 'min_possession_length_frames' frames
    team_possessions = 1*( (lastTouch==team) & (live) ) # team was last team to touch ball, and the ball is in play
    team_possessions = np.diff( 1*( np.convolve( team_possessions, np.ones(min_possession_length_frames), mode='same' ) >= min_possession_length_frames ) ) # this is a trick for finding sequences of consecutive frames that meet some condition and extends for at least a specified minimum duration
    team_possessions_start = np.where( team_possessions == 1 )[0] - int(min_possession_length_frames/2) + 1 # adding min_possession_length_frames/2 because of the way that the convolution is centred
    team_possessions_end = np.where( team_possessions == -1 )[0] + int(min_possession_length_frames/2) + 1
    return team_possessions_start, team_possessions_end

def index_of_substitution(team, frames):
    # check whether a substitution is made during frames. Formation analysis can't handle personnel changes, so formations must be measured seperately before and after substitutions
    players_in_first_frame = frames.iloc[0].homePlayers if team=='home' else frames.iloc[0].awayPlayers
    players_in_first_frame = set( [p['number'] for p in players_in_first_frame] )
    for i,frame in frames.iterrows():
        players = frame.homePlayers if team=='home' else frame.awayPlayers
        player_in_frame = set( [p['number'] for p in players] )
        if players_in_first_frame != player_in_frame:
            print( '%s team substitution occured on %d minutes:' % (team,(frame.period-1)*45+np.ceil(frame.gameClock/60.)))
            print( '    players off: ',players_in_first_frame - player_in_frame)
            print( '    players on : ', player_in_frame - players_in_first_frame)
            print( 'ending formation measure here' )
            break
    return i

class formation(object):
    ''' this is the data structure that calculates and holds the formation measure '''
    def __init__(self,team,gk):
        self.lattices = [] # a list of 'lattices' or instantaneous formation measures (which will be averaged to get the final formation observations)
        self.nlattices = 0
        self.gk = gk # gk is a list of the gk jersey numbers (so we know which players to exclude for the outfield formation measure). Is a list because the gk might get substituted or sent off.
        self.team = team # team name variable (just to keep track of which forrmation is which)
        self.is_cluster_template = False # until set True
        
      
    def add_latice(self,lattice):
        if len( self.lattices ) == 0:
            self.pids = set( lattice.pids )
        else:
            if set( lattice.pids ) != self.pids:
                print( set( lattice.pids ), self.pids )
                assert False
        self.lattices.append(lattice)
        self.nlattices = len(self.lattices)
        
    def delete_lattices(self):
        self.lattices = []
    
    def to_com_frame(self):
        self.xcom = 0.
        self.ycom = 0
        for pid in self.pids:
            self.xcom += self.nodes[pid].x
            self.ycom += self.nodes[pid].y
        self.xcom = self.xcom/float(len(self.pids))
        self.ycom = self.ycom/float(len(self.pids))
        for pid in self.pids:
            self.nodes[pid].x = self.nodes[pid].x - self.xcom
            self.nodes[pid].y = self.nodes[pid].y - self.ycom
        
    def calc_average_lattice(self,match,n_neighbours=3):
        # calculates formation from all the individual formation observations (lattices)
        self.nodes = {}
        self.nlattices = len(self.lattices)
        # find average distance to 'n_neighbours' nearest neighbour
        # iterate over each player
        for p in self.pids:
            newnode = node(p,np.nan,np.nan) # create new node for player in averaged forrmation
            for n in self.pids:
                if n!=p:
                    px = []
                    py = []
                    for lattice in self.lattices:
                        # calculate distance to all other players
                        px.append( lattice.nodes[p].neighbours[n][1] ) # x diff
                        py.append( lattice.nodes[p].neighbours[n][2] ) # y diff
                    newnode.add_neighbour(n,np.median(px),np.median(py)) # take median vector
            # sort by nearest neighbours
            newnode.sort_neighbours()
            newnode.calc_local_density(n_neighbours)
            self.nodes[p] = newnode
        self.pids = list(self.pids)
        # sort nodes by local density
        self.pids = sorted(self.pids,key = lambda x: self.nodes[x].local_density, reverse=False  )
        # start with highest density node: call that the reference node (or player) 
        reference_player = self.pids[0]
        self.nodes[reference_player].x = 0.0 # put the reference player at center of pitch for now
        self.nodes[reference_player].y = 0.0
        # find positions of all players relative to this player
        for pid in self.pids[1:]:
            self.nodes[pid].x = self.nodes[reference_player].neighbours[pid][1]
            self.nodes[pid].y = self.nodes[reference_player].neighbours[pid][2]
        # finally transform so that centre of mass of formation is at centre of field
        self.to_com_frame()
        
    def plot_formation(self,metadata,figax=None,title=None,labels=True,pc='r',MarkerSize=10,alpha=0.5):
        # plot the formation
        if figax is None:
            fig,ax = viz.plot_pitch(metadata)
        else:
            fig,ax = figax
        factor = 1
        for pid in self.pids:
            x = self.nodes[pid].x 
            y = self.nodes[pid].y
            ax.plot(x,y,pc+'o',MarkerSize=MarkerSize,alpha=alpha)
            if labels:
                ax.text(x+factor*0.5,y+factor*0.5,pid,color=pc)
        if title is not None:
            fig.suptitle(title,y=0.95,fontsize=14,color=pc)
    

class lattice(object):
    # a measure of a team's formation at a single instant (i.e. tracking data frame)
    def __init__(self,players,exclude,timestamp,flip=1.0,units=1.):
        self.direction_flip = flip
        self.players = [p for p in players if p['number'] not in exclude]
        self.timestamp = timestamp 
        self.exclude = exclude
        self.nodes = {}
        self.formation_offset_nodes = {}
        self.add_nodes(units)
        self.calc_com()
        self.calc_edges()
        self.to_com()
        
    def add_nodes(self,units):
        for p in self.players:
            px = p['xyz'][0]/units*self.direction_flip
            py = p['xyz'][1]/units*self.direction_flip
            self.nodes[p['number']] = node(p['number'],px,py)
        self.pids = list( self.nodes.keys() )
        
    def add_formation_offset_nodes(self,pid,dx,dy):
        self.formation_offset_nodes[pid] = node(pid,dx,dy)
         
            
    def calc_edges(self):
        for p in self.pids:
            for n in self.pids:
                if p!=n:
                    dx = self.nodes[n].x - self.nodes[p].x
                    dy = self.nodes[n].y - self.nodes[p].y
                    self.nodes[p].add_neighbour(self.nodes[n].pid,dx,dy)
            #self.nodes[p].sort_neighbours()
    
    def calc_com(self):
        self.xcom = 0.
        self.ycom = 0.
        for p in self.pids:
            self.xcom += self.nodes[p].x
            self.ycom += self.nodes[p].y
        self.xcom = self.xcom/float(len(self.pids))
        self.ycom = self.ycom/float(len(self.pids))
        
    def get_com(self,exclude=[]):
        xcom = 0.
        ycom = 0.
        for p in self.pids:
            if p not in exclude:
                xcom += self.nodes[p].x + self.xcom
                ycom += self.nodes[p].y + self.ycom
        xcom = xcom/float(len(self.pids)-len(exclude))
        ycom = ycom/float(len(self.pids)-len(exclude))
        return xcom,ycom
     
    def from_com(self):
        for p in self.pids:
            self.nodes[p].x += self.xcom
            self.nodes[p].y += self.ycom
     
    def to_com(self):
        for p in self.pids:
            self.nodes[p].x -= self.xcom
            self.nodes[p].y -= self.ycom

    

class node(object):
    # a single player in the formation
    def __init__(self,pid,px,py):
        self.pid = pid
        self.neighbours = {}
        self.x = px
        self.y = py
        
    def has_position(self):
        return ~np.isnan(self.x) and ~np.isnan(self.y)        
        
    def add_neighbour(self,pid,dx,dy):
        dist = np.sqrt(dx*dx+dy*dy)
        self.neighbours[pid] = (pid,dx,dy,dist)
        
    def sort_neighbours(self):
        self.nearest_neighours = [self.neighbours[p] for p in self.neighbours.keys()]
        self.nearest_neighours = sorted(self.nearest_neighours,key = lambda x: x[3])
     
    def calc_local_density(self,N):
        # average distance to N nearest neighbours
        #self.local_density = np.sum([x[3] for x in self.nearest_neighours[:N]])/float(N)
        self.local_density = self.nearest_neighours[N-1][3]
     
    def __repr__(self):
        print(self.pid)
        