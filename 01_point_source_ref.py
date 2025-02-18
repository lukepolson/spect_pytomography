#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.spect.ge_discovery_nm670 as nm670
from pathlib import Path
from helpers import add_point_source

if __name__ == "__main__":

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True  # uncomment to enable visualisation
    sim.visu_type = "qt"
    # sim.visu_type = "vrml"
    sim.random_seed = "auto"
    # with a lot of runs, using MT is *NOT* recommended
    sim.number_of_threads = 1
    sim.progress_bar = True
    sim.output_dir = Path("output") / "01_point_source_ref"
    sim.store_json_archive = True
    sim.store_input_files = False
    sim.json_archive_filename = "simu.json"

    # units
    sec = gate.g4_units.s
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq

    # options
    activity = 2e5 * Bq / sim.number_of_threads
    n = 60
    total_time = 200 * sec
    radius = 16 * cm

    # visu
    if sim.visu:
        total_time = 1 * sec
        sim.number_of_threads = 1
        activity = 100 * Bq

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # set the two spect heads
    heads, crystals = nm670.add_spect_two_heads(
        sim, "spect", collimator_type="lehr", debug=sim.visu == True
    )

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 100 * mm)
    sim.physics_manager.set_production_cut(crystals[0].name, "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystals[1].name, "all", 2 * mm)

    # add point source
    source = add_point_source(sim, "src", heads, "tc99m", activity)

    # digitizer : probably not correct (yet)
    projs = []
    for i in range(2):
        digit = nm670.add_digitizer_tc99m_v2(
            sim, crystals[i], f"digit_{i}", spectrum_channel=False
        )
        proj = digit.find_module(f"digit_{i}_projection")
        proj.output_filename = f"projection_{i}.mhd"
        projs.append(proj)

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.output_filename = f"stats.txt"

    # set the rotation angles (runs)
    step_time = total_time / n
    sim.run_timing_intervals = [[i * step_time, (i + 1) * step_time] for i in range(n)]

    # compute the gantry rotations
    step_angle = 180 / n
    nm670.rotate_gantry(heads[0], radius, 0, step_angle, n)
    nm670.rotate_gantry(heads[1], radius, 180, step_angle, n)

    # options to make it faster, but unsure if the geometry is correct
    # With a honeycomb collimator: geant4 optimisation take forever ; we can disable (dyn_geom_open_close = False)
    # but I am not sure if the result is correct
    # sim.dyn_geom_open_close = False
    # sim.dyn_geom_optimise = False

    # go
    sim.run()
    print(stats)
    print(f"Projections saved in {[proj.get_output_path() for proj in projs]}")
