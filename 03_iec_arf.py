#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.spect.ge_discovery_nm670 as nm670
import opengate.contrib.phantoms.nemaiec as iec
from pathlib import Path
import SimpleITK as sitk
from opengate.contrib.spect.ge_discovery_nm670 import add_arf_detector
from opengate.contrib.spect.spect_helpers import (
    merge_several_heads_projections,
    extract_energy_window_from_projection_actors,
)

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
    sim.output_dir = Path("output") / "03_iec_arf"

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
    total_time = 200 * sec
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
    pth = Path("pth") / "arf_034_nm670_tc99m.pth"
    det_plane1, arf1 = add_arf_detector(
        sim, radius, 0, size, spacing, "lehr", "detector", 1, pth
    )
    det_plane2, arf2 = add_arf_detector(
        sim, radius, 180, size, spacing, "lehr", "detector", 2, pth
    )
    det_planes = [det_plane1, det_plane2]
    arfs = [arf1, arf2]

    # phantom
    phantom = iec.add_iec_phantom(sim, name="phantom")

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 100 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 5 * mm)

    # add iec source
    activity_Bq_mL = [activity] * 6
    sources = iec.add_spheres_sources(
        sim, phantom.name, "sources", "all", activity_Bq_mL, verbose=True
    )
    total_activity = 0
    for source in sources:
        gate.sources.generic.set_source_rad_energy_spectrum(source, "tc99m")
        source.particle = "gamma"
        source.direction.acceptance_angle.volumes = [h.name for h in det_planes]
        source.direction.acceptance_angle.skip_policy = "SkipEvents"
        source.direction.acceptance_angle.intersection_flag = True
        total_activity += source.activity
    total_activity *= sim.number_of_threads
    print(f"Total activity is {total_activity / kBq:.0f} kBq")
    print(f"Total activity is {total_activity / MBq:.1f} MBq")

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

    # extract energy window images
    energy_window = 1
    filenames = extract_energy_window_from_projection_actors(
        arfs, energy_window=energy_window, nb_of_energy_windows=2, nb_of_gantries=n
    )

    # merge two heads
    output_img = merge_several_heads_projections(filenames)
    sitk.WriteImage(output_img, sim.output_dir / f"projections_ene_{energy_window}.mhd")
