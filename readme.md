

# test01 

- SPECT GE NM670 with 2 heads
- digitizer for Tc99m (2 energy windows)
- point source in air (no phantom), tc99m as a source of gamma 140 keV
- head distance is 16 cm
- rotation of 60 x 2 angles
- projections are merged into one single files at the end 
- 2e5 Bq during 200 sec = 35.4 millions primaries
- do *not* use multithreading here (because several runs)
- slow due to Geant4 "optimisation" of honeycomb collimator ; I dont know how to disable it


# test02

- same as test01 with ARF instead of full spect head
- ARF (Angular Response Function) are trained from data generated with test00
- 2xfaster than test01 + less particles needed for the same variance (around x5 faster)


# test03

- same than test02 with ARF and IEC 6 spheres phantom

