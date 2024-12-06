#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import SimpleITK
import itk
import numpy as np
from pathlib import Path

from opengate.image import resample_itk_image
from opengate.contrib.dose.photon_attenuation_image_helpers import (
    create_photon_attenuation_image,
)
from opengate.contrib.spect.pytomography_helpers import osem_pytomography
from opengate.contrib.spect.spect_helpers import read_projections_as_sinograms

if __name__ == "__main__":

    # input folder
    projections_folder = Path("output") / "03_iec_arf"
    size = [128, 128, 128]
    spacing = [4.42, 4.42, 4.42]

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

    # generate attenuation map
    # opengate_photon_attenuation_image -i data/iec_1mm.mhd -l data/iec_1mm.json -o mumap.mhd
    input_ct = Path("data") / "iec_1mm.mhd"
    labels_filename = Path("data") / "iec_1mm_labels.json"
    material_database = Path("data") / "iec_1mm.db"
    attenuation_image = create_photon_attenuation_image(
        input_ct,
        labels_filename,
        energy=0.1405,
        material_database=material_database,
        database="EPDL",
        verbose=True,
    )
    attenuation_image = resample_itk_image(
        attenuation_image, size, spacing, default_pixel_value=0, linear=True
    )
    att_filename = projections_folder / "mumap.mhd"
    itk.imwrite(attenuation_image, att_filename)

    # osem reconstruction
    options = {
        "size": size,
        "spacing": spacing,
        "n_iters": 4,
        "n_subsets": 8,
        "collimator_name": "G8-LEHR",  # "SY-LEHR",
        "energy_kev": 140.5,
        "intrinsic_resolution_cm": 0.38,
        "attenuation_image": str(att_filename),
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
    print(f"vv data/iec_1mm.mhd --fusion {output}")
