Those are the scripts used for the generation and plotting of the data presented in ``Magic State Injection with Erasure Qubits'' ([arXiv:2504:02935](https://arxiv.org/abs/2504.02935)).

Since some scripts are using the code published by Gidney in the "Cleaner magic states with hook injection" paper, first run `step0_clone_Gidney_repo` to clone its repo into the `gidney_code` folder.

Figure 3a & 7:
- The data was collected using `expand_script.py`.
- Collected data in `out/expand_raw,*,2025-01-30,batch_size=500.csv`.
- Plotting tools in `expand_plot.ipynb`.

Figure 3b:
- Data generation tools in `end2end_script.py`.
- Data in `out/pareto_raw,*,2024-12-15,batch_size=500.csv`.
- Plotting tools in `plot_pareto.ipynb`.

Figure 4 & 12:
- Data in `out/2024-12-21-erasuremagic_1e6runs_sj` for distance 3.
- Data in `out/2025-07-17-erasuremagic_5e5runs_d=5` for distance 5.
- Data in `out/2025-07-17-erasuremagic_5e5runs_d=7` for distance 7.
- Plotting tools in `Erasuremagic.ipynb`.

Figure 5:
- To decide which qubits to declare as erasure qubits, the notebook `Combination_searching.ipynb` was used.
- To simulate and plot the result, the notebook `cultivation.ipynb` was used.

Figure 6:
- The qpic code for the figure is given in `qpic` folder.

Figure 2 & 8 & 9:
- Data in `out/2024-12-24-compare_injections_5e6runs_2erasures` and `out/2025-07-13-compare_injections_25e5runs_1erasure`.
- Plotting tools in `compare_injections.ipynb` & `compare_injections-vary_distance.ipynb`.

Figure 10:
- To simulate and plot the result, the notebook `error_counter.ipynb` was used.