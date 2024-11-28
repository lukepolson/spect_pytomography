# test00

- simulation to generate a training database for the ARF
- the trained arf net is used in following tests

# test01 

- SPECT GE NM670 with 2 heads
- digitizer for Tc99m (2 energy windows).
- point source in air (no phantom), tc99m as a source of gamma 140 keV
- head distance is 16 cm
- rotation of 60 x 2 angles
- 2e5 Bq during 200 sec = 35.4 millions Bq
- do *not* use multithreading here (because several runs)
- slow due to Geant4 "optimisation" of honeycomb collimator ; I don't know how to disable it
- (about 11 min comp time on my linux)


# test02

- same as test01 with ARF instead of full spect head
- ARF (Angular Response Function) are trained from data generated with test00
- faster than test01. Moreover, ARF needs fewer particles for the same variance, it is thus even possible to run 
less particles (around x5 less) and scale the result to obtain similar variance (not done here).
- (about 2 min comp time on my linux)


# test03, test04

- same than test02 with ARF and IEC 6 spheres phantom
- 3D image is reconstructed in test04

# test05

- check test03 with voxelized phantom and voxelized source 
- much slower (x3)
- current is 100 sec instead of 200 sec

Comparison: 

    vv data/iec_1mm.mha --fusion output/03_iec_arf/reconstructed.mhd data/iec_1mm.mha --fusion output/05_iec_vox_arf/reconstructed.mhd --linkall&