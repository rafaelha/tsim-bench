def test_synd_ext():
    code = BBCode.from_n(144)
    backend = BaseBackend.from_noise_level(0.0)
    sim = BBMemSimulator(code, 1, backend)
    c = stim.Circuit()
    aut = TourBBAut.from_n(144)
    lxs = aut.get_logical_qubits("X")
    lzs = aut.get_logical_qubits("Z")
    lxs_supp = [lx.to_vec().nonzero()[0].tolist() for lx in lxs]
    lzs_supp = [lz.to_vec().nonzero()[0].tolist() for lz in lzs]
    mem_exp_base = "Z"
    c.append_operation(f"R{mem_exp_base}", code.all_dat_uids)
    c.append("TICK")
    c = sim.apply_all_checks(c)
    c.append("TICK")
    sim.apply_meas_and_record_abs_ids(c, mem_exp_base, code.all_dat_uids)
    print(c)
    logical_supps = lzs_supp if mem_exp_base == "Z" else lxs_supp
    sim.apply_observables(c, mem_exp_base, logical_supps)
    dem = c.detector_error_model()
    print(dem)
