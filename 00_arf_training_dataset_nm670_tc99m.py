#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import opengate.contrib.spect.ge_discovery_nm670 as nm670
import opengate as gate

if __name__ == "__main__":

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True
    sim.visu_type = "qt"
    sim.number_of_threads = 4
    sim.output_dir = Path("output") / "00_arf_training_dataset_nm670"
    sim.progress_bar = True
    sim.store_json_archive = True
    sim.store_input_files = False
    sim.json_archive_filename = "simu.json"

    # units
    nm = gate.g4_units.nm
    mm = gate.g4_units.mm
    m = gate.g4_units.m
    cm = gate.g4_units.cm
    Bq = gate.g4_units.Bq
    MeV = gate.g4_units.MeV

    # activity
    activity = 5e8 * Bq / sim.number_of_threads
    if sim.visu:
        sim.number_of_threads = 1
        activity = 1e3 * Bq
        sim.output_dir = Path("output") / "visu"

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect head
    colli_type = "lehr"
    head, colli, crystal = nm670.add_spect_head(
        sim, "spect", collimator_type=colli_type, debug=sim.visu == True
    )
    print("Head position", head.translation)

    # digitizer
    digit = nm670.add_digitizer_tc99m_v2(
        sim, crystal, f"digitizer", spectrum_channel=False
    )
    ew = digit.find_module(f"digitizer_energy_window")
    proj = digit.find_module(f"digitizer_projection")
    proj.write_to_disk = False

    # arf actor for building the training dataset
    detector_plane, arf = nm670.add_actor_for_arf_training_dataset(
        sim, head, colli_type, ew, rr=50
    )
    print("Plane position", detector_plane.translation)

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option4"
    sim.physics_manager.global_production_cuts.all = 1 * mm

    # source for training dataset
    source = nm670.add_source_for_arf_training_dataset(
        sim, "src", activity, detector_plane, 0.01 * MeV, 0.154 * MeV
    )
    print("Source position", source.position.translation)

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.output_filename = "stats.txt"

    # start simulation
    sim.run()

    # print results at the end
    print(stats)

    # print cmd line to train GARF
    pth_json = "pth/train_arf_v034.json"
    pth = "pth/arf_034_nm670_tc99m.pth"
    print(f"garf_train {pth_json} {arf.get_output_path()} {pth}")
