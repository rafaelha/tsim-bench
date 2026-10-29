# QLDPC codes magic state injection.

## Install Locally, use anywhere (recommend)

1. Create your own conda environment with Python version == 3.12
```bash
conda create -n your_env_name python=3.12
```

2. Install this package locally:
```bash
pip install -e .
```

__Note__: Install `sinter==1.13.0`. Latest version does not work due to a known bug when setting post-selection mask. See [here](https://quantumcomputing.stackexchange.com/questions/44364/how-to-use-sinter-to-collect-stats-with-postselection).

## Reproducibility of the results in the paper

### Init config relevant

Under folder `prj_msi/10find_cfg`.

**Find init configs**
```bash
python prj_msi/10find_cfg/find_cfg_v2.py -c bb-n144
python prj_msi/10find_cfg/find_cfg_v2.py -c bb-n144 -n li_twoq_dominant
python prj_msi/10find_cfg/find_cfg_v2.py -c bb-n144 -m mfs
python prj_msi/10find_cfg/find_cfg_v2.py -c xu-hgp-n225
```

**Find best init configs**
```bash
python prj_msi/10find_cfg/best_cfg.py -c bb-n144
python prj_msi/10find_cfg/best_cfg.py -c bb-n144 -n li_twoq_dominant
python prj_msi/10find_cfg/best_cfg.py -c xu-hgp-n225
```

**Compare fixed stabilizer finding methods: max-fixed-stabs and max-supp-protection**
```bash
python prj_msi/10find_cfg/cmp_fixing_methods.py
```

### Circuit-level simulations relevant

Under folder `prj_msi/20sim`.

**Simulate MSI**
```bash
python prj_msi/20sim/inject_y_v2.py
python prj_msi/20sim/inject_y_v2.py -n li_twoq_dominant
python prj_msi/20sim/inject_y_v2_xu_hgp.py
```

**Visualize Scalability**
```bash
python prj_msi/20sim/scalability.py
python prj_msi/20sim/scalability.py -n li_twoq_dominant
python prj_msi/20sim/scalability_xu_hgp.py
```

**Analyze and visualize correlated errors**
Under folder `prj_msi/93inject_4logicals`:

Simulation:
```bash
python prj_msi/93inject_4logicals/inject_y_w_correlated_errors.py
```

Visualization:
```bash
python prj_msi/93inject_4logicals/breakdown_corr_errs.py
```

### Discard rate relevant

```bash
python prj_msi/20sim/why_similar_discard_rates.py
```

## Public Package Entry Points

Design principle: 
1. Each code family has its own submodule, and the submodule has its own facade, and the facade is the only public entry point for that code family.
2. Common utilities are shared in the root package.

Example: 
1. BB codes are in `qldpc_msi.tour_bb`, and the public entry point is `qldpc_msi.tour_bb.facade`.
2. Code-independent utilities are in the `qldpc_msi.{msi,codes,circuits,qec_toolkit,...}` submodules.

Project scripts should import from the code-family facades instead of family internals.

```python
from qldpc_msi import tour_bb, xu_hgp

bb_code = tour_bb.make_code(n=144)
bb_circ = tour_bb.build_msi_circuit(
    bb_code,
    init_cfg=cfg,
    n_cycles=3,
    remove_dummy_cnots=False,
    se_variant="interleaved",
)

hgp_code = xu_hgp.make_code(n=225)
hgp_circ = xu_hgp.build_msi_circuit(
    hgp_code,
    init_cfg=cfg,
    n_cycles=3,
    se_variant="product_coloration",
    error_params=error_params,
)
```

Module-boundary guidance lives in [`docs/module-boundary-criteria.md`](./docs/module-boundary-criteria.md).
