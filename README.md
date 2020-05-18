# SecondSpectrum
Code for measuring formations with second spectrum data

See the example script SecondSpectrum_Formation_Script.py for generating formations from second spectrum tracking data.

Methodology is based on that described here: https://static.capabiliaserver.com/frontend/clients/barca/wp_prod/wp-content/uploads/2020/01/56ce723e-barca-conference-paper-laurie-shaw.pdf

In short, the algorithm aggregates possessions together for each team, and then measures the offensive (in possession) and defensive (out of possession) formation for a team over these possessions. You specify the time period in the match over which you want to measure the formations. 

The code can't currently handle substitutions, so you have to measure formations before and after a team makes a substitution separately (you may want to do this anyway: substitutions are often indicative of a change in formation).

Modules include:
----------------
SecondSpectrum_IO.py: functions for reading in and some basic processing of tracking data

SecondSpectrum_Viz.py: creating a pitch and plotting player positions

SecondSpectrum_Formations.py: measuring the offensive (in possession) and defensive (out of possession) formations of a team in a specified period of the match
