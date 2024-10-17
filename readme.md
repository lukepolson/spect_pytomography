

# test01 

- SPECT GE NM670 with 2 heads
- digitizer for Tc99m (2 energy windows).
- point source in air (no phantom), tc99m as a source of gamma 140 keV
- head distance is 16 cm
- rotation of 60 x 2 angles
- projections are merged into one single files at the end 
- 2e5 Bq during 200 sec = 35.4 millions Bq
- do *not* use multithreading here (because several runs)
- slow due to Geant4 "optimisation" of honeycomb collimator ; I dont know how to disable it
- (about 11 min comp time on my linux)


# test02

- same as test01 with ARF instead of full spect head
- ARF (Angular Response Function) are trained from data generated with test00
- faster than test01. Moreover, ARF needs less particles for the same variance, it is thus even possible to run 
less particles (around x5 less) and scale the result to obtain similar variance (not done here).
- (about 2 min comp time on my linux)


# test03

- same than test02 with ARF and IEC 6 spheres phantom


# test00

- simulation to generate a training database for the ARF
- the trained arf net is used in test02 and test03