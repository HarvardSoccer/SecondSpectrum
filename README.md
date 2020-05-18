# SecondSpectrum
Code for measuring formations with second spectrum data

See the example script SecondSpectrum_Formation_Script.py for generating formations from second spectrum tracking data.

Methodology is based on that described here: https://static.capabiliaserver.com/frontend/clients/barca/wp_prod/wp-content/uploads/2020/01/56ce723e-barca-conference-paper-laurie-shaw.pdf

Modules include:
----------------
SecondSpectrum_IO.py: functions for reading in and some basic processing of tracking data

SecondSpectrum_Viz.py: creating a pitch and plotting player positions

SecondSpectrum_Formations.py: measuring the offensive (in possession) and defensive (out of possession) formations of a team in a specified period of the match
