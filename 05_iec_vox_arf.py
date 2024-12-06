#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.spect.ge_discovery_nm670 as nm670
import opengate.contrib.phantoms.nemaiec as nemaiec
from opengate.image import get_translation_to_isocenter
from opengate.sources.base import set_source_rad_energy_spectrum
from pathlib import Path
import numpy as np


if __name__ == "__main__":

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True # uncomment to enable visualisation
    sim.visu_type = "qt"
    # sim.visu_type = "vrml"
    sim.random_seed = "auto"
    # with a lot of runs, using MT is *NOT* recommended
    sim.number_of_threads = 1
    sim.progress_bar = True
    sim.output_dir = Path("output") / "05_iec_vox_arf"
    sim.store_json_archive = True
    sim.store_input_files = False
    sim.json_archive_filename = "simu.json"

    # units
    sec = gate.g4_units.s
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq
    kBq = Bq * 1e3
    MBq = Bq * 1e6
    cm3 = gate.g4_units.cm3
    BqmL = Bq / cm3

    # options
    activity = 1e5 * BqmL / sim.number_of_threads
    n = 60
    total_time = 100 * sec
    radius = 20 * cm

    # visu
    if sim.visu:
        total_time = 1 * sec
        sim.number_of_threads = 1
        activity = 1 * BqmL / sim.number_of_threads

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # set the two spect heads
    spacing = [2.21 * mm * 2, 2.21 * mm * 2]
    size = [128, 128]
    pth = Path("pth") / "arf_034_nm670_tc99m_v2.pth"
    det_plane1, arf1 = nm670.add_arf_detector(
        sim, radius, 0, size, spacing, "lehr", "detector", 1, pth
    )
    det_plane2, arf2 = nm670.add_arf_detector(
        sim, radius, 180, size, spacing, "lehr", "detector", 2, pth
    )
    det_planes = [det_plane1, det_plane2]
    arfs = [arf1, arf2]

    # IEC voxelization
    # voxelize_iec_phantom -o data/iec_1mm.mhd --spacing 1 --output_source data/iec_1mm_activity.mhd -a 1 1 1 1 1 1
    # voxelize_iec_phantom -o data/iec_4.42mm.mhd --spacing 4.42 --output_source data/iec_4.42mm_activity.mhd -a 1 1 1 1 1 1
    # voxelize_iec_phantom -o data/iec_4mm.mhd --spacing 4 --output_source data/iec_4mm_activity.mhd -a 1 1 1 1 1 1

    # phantom
    iec_vox_filename = Path("data") / "iec_4mm.mhd"
    iec_label_filename = Path("data") / "iec_4mm_labels.json"
    db_filename = Path("data") / "iec_4mm.db"
    vox = sim.add_volume("ImageVolume", "phantom")
    vox.image = iec_vox_filename
    vox.read_label_to_material(iec_label_filename)
    vox.translation = get_translation_to_isocenter(vox.image)
    sim.volume_manager.add_material_database(str(db_filename))

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 100 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 5 * mm)

    # add iec voxelized source
    iec_source_filename = Path("data") / "iec_1mm_activity.mhd"
    source = sim.add_source("VoxelSource", "src")
    source.image = iec_source_filename
    source.position.translation = [0, 35 * mm, 0]
    set_source_rad_energy_spectrum(source, "tc99m")
    source.particle = "gamma"
    source.direction.acceptance_angle.volumes = [h.name for h in det_planes]
    source.direction.acceptance_angle.skip_policy = "SkipEvents"
    source.direction.acceptance_angle.intersection_flag = True
    _, volumes = nemaiec.get_default_sphere_centers_and_volumes()
    source.activity = activity * np.array(volumes).sum()
    print(f"Total activity is {source.activity/ Bq}")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.output_filename = f"stats.txt"

    # set the rotation angles (runs)
    step_time = total_time / n
    sim.run_timing_intervals = [[i * step_time, (i + 1) * step_time] for i in range(n)]

    # compute the gantry rotations
    step_angle = 180 / n
    nm670.rotate_gantry(det_plane1, radius, 0, step_angle, n)
    nm670.rotate_gantry(det_plane2, radius, 180, step_angle, n)

    # options to make it faster, but unsure if the geometry is correct
    # sim.dyn_geom_open_close = False
    # sim.dyn_geom_optimise = False

    # go
    sim.run()
    print(stats)
