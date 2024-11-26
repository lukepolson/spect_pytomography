#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import SimpleITK
import numpy as np
from pathlib import Path
from opengate.contrib.spect.pytomography_helpers import osem_pytomography
from opengate.contrib.spect.spect_helpers import read_projections_as_sinograms

if __name__ == "__main__":

    # input folder
    projections_folder = Path("output.save") / "03_iec_arf_200sec"

    # input projections from GATE simulation (two heads)
    projections_filenames = ("projection_1.mhd", "projection_2.mhd")
    start_angle = 90  # initial rotation in gate
    nb_of_gantry_angles_per_head = 60
    nb_of_gantry_angles = nb_of_gantry_angles_per_head * len(projections_filenames)
    print("Reading sinograms from the 2 heads")
    sinograms = read_projections_as_sinograms(
        projections_folder, projections_filenames, nb_of_gantry_angles_per_head
    )
    nb_of_energy_windows = len(sinograms)
    print(
        f"Found {nb_of_energy_windows} energy windows with {nb_of_gantry_angles} angles"
    )

    # consider the peak energy windows only for the moment
    sinogram = sinograms[1]
    print(f"Projections size={sinogram.GetSize()} spacing={sinogram.GetSpacing()}")

    # osem reconstruction
    options = {
        "size": [128, 128, 128],
        "spacing": [4.42, 4.42, 4.42],
        "n_iters": 4,
        "n_subsets": 8,
        "collimator_name": "SY-LEHR",
        "energy_kev": 140.5,
        "intrinsic_resolution_cm": 0.38,
    }
    angles_deg = np.linspace(
        -start_angle, -start_angle + 360, nb_of_gantry_angles, endpoint=False
    )
    radii_cm = np.ones(nb_of_gantry_angles) * 20

    print(
        f'Start OSEM with {options["n_iters"]} iterations and {options["n_subsets"]} subsets'
    )
    recon = osem_pytomography(sinogram, angles_deg, radii_cm, options)

    output = projections_folder / "reconstructed.mhd"
    print(f"Save reconstructed image in {output}")
    SimpleITK.WriteImage(recon, output)

    print()
    print(f"vv data/iec_1mm.mha --fusion {output}")
