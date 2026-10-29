import sinter
from stimbposd import SinterDecoder_BPOSD

from .pipelined_se_test import H_rep3, visualize_layout
from .product_se import make_xu_hgp_product_coloration_se_circuit_uid


def test_rep3_memory_experiment():
    H = H_rep3()
    c, _, layout = make_xu_hgp_product_coloration_se_circuit_uid(
        H,
        n_rounds=2,
        include_qubit_coords=False,
        add_time_detectors=True,
        validate_keys=True,
    )
    visualize_layout(layout, show_uid=True)
    print("c:")
    print(c)

    # This catches many wiring mistakes by forcing stim to validate detector references.
    _ = c.compile_detector_sampler()
    p = 0.001
    tasks = [
        sinter.Task(
            circuit=c,
            json_metadata={
                "p": p,
            },
            decoder=f"bposd",
        )
    ]
    decoder = SinterDecoder_BPOSD(
        max_bp_iters=1000,
        bp_method="ms",
        osd_order=10,
        osd_method="osd_cs",
        ms_scaling_factor=0,
    )
    n_shots = 1000
    ana_corr_err = False
    verbose = True

    stats: list[sinter.TaskStats] = sinter.collect(
        num_workers=1,
        tasks=tasks,
        decoders=["bposd"],
        max_shots=n_shots,
        max_errors=None,  # avoid early stopping dominated by the easiest-to-fail observable
        custom_decoders={"bposd": decoder},
        count_observable_error_combos=ana_corr_err,  # decompose the error into observable error combinations
        print_progress=verbose,
    )
    return stats
