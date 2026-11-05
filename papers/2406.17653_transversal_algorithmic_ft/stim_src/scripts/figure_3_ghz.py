import numpy as np
import statsmodels.stats.proportion
import matplotlib.pyplot as plt

def figure_error_rate_vs_distance():
    tex_fonts = {
        # Use LaTeX to write all text
        "text.usetex": False,
        "font.family": 'sans-serif',  # Helvetica Neue',
        'font.sans-serif': "Helvetica",
        # Use 10pt font in plots, to match 10pt font in document
        "axes.labelsize": 7,
        "font.size": 7,
        # Make the legend/label fonts a little smaller
        "legend.fontsize": 5,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7
    }
    plt.rcParams.update(tex_fonts)
    fig, ax = plt.subplots(1, 1, sharey=True, sharex=True, figsize=(1.5, 1.85))

    transversal_correct_mle = np.array([0.0711*10000, 0.0313*10000, 0.0121*10000, 0.0052*10000, 0.0018*10000+0.0022333333333333333*40000,
                                        0.0005*10000+0.001*20000+0.00075*40000])
    transversal_total_mle = np.array([10000, 10000, 10000, 10000, 50000, 70000])
    lb_transversal_mle, ub_transversal_mle = statsmodels.stats.proportion.proportion_confint(transversal_correct_mle,
                                                                                             transversal_total_mle)

    lattice_surgery_correct_mle = np.array([0.144, 0.206, 0.258, 0.276, 0.326, 0.347]) * 1000
    lattice_surgery_total_mle = np.ones_like(lattice_surgery_correct_mle) * 1000
    lb_lattice_surgery_mle, ub_lattice_surgery_mle = statsmodels.stats.proportion.proportion_confint(lattice_surgery_correct_mle,
                                                                                             lattice_surgery_total_mle)

    plotline, cap, barlinecols = plt.errorbar(np.arange(3, 15, 2), (lattice_surgery_correct_mle / lattice_surgery_total_mle),
                                              yerr=[
                                                  (lattice_surgery_correct_mle / lattice_surgery_total_mle - lb_lattice_surgery_mle),
                                                  (ub_lattice_surgery_mle - lattice_surgery_correct_mle / lattice_surgery_total_mle)],
                                              label='Lattice surgery', marker='o', markerfacecolor='#FEEACF',
                                              markeredgecolor='#E5B887', color='#E5B887',
                                              linewidth=.75, markersize=3, markeredgewidth=.5)
    plt.setp(barlinecols[0], capstyle="round")

    plotline, cap, barlinecols = plt.errorbar(np.arange(3, 15, 2), (transversal_correct_mle / transversal_total_mle),
                                              yerr=[
                                                  (transversal_correct_mle / transversal_total_mle - lb_transversal_mle),
                                                  (ub_transversal_mle - transversal_correct_mle / transversal_total_mle)],
                                              label='Transversal', marker='o', markerfacecolor='#8EA5B8',linewidth=.75, markeredgewidth=.5,
                                              markeredgecolor='#54738D', color='#8EA5B8', markersize=3)
    plt.setp(barlinecols[0], capstyle="round")

    ax.semilogy()
    ax.set_ylim(.5e-4, .55)
    ax.set_ylim(.8e-4, .55)
    ax.set_xlabel('Code distance', labelpad=-0.5)
    ax.set_ylabel('Logical error rate', labelpad=0.5)

    ax.tick_params(axis='y', which='major', pad=0.5)
    ax.tick_params(axis='y', which='minor', pad=-1.0)
    ax.tick_params(axis='x', which='major', pad=0.5)
    ax.set_xticks([3, 5, 7, 9, 11, 13])
    plt.setp(ax.get_xminorticklabels(), visible=False)
    ax.legend(frameon=False, loc='lower left', handlelength=1., handletextpad=0.5, labelspacing=0.5,#(.35, .6)
              borderpad=.1, fontsize=6)
    plt.tight_layout()
    plt.subplots_adjust(left=.24, right=.97)
    ax.tick_params(axis='y', which='minor', left=False)

    plt.savefig('figs/figure_3_ghz.pdf')
    # plt.show()

figure_error_rate_vs_distance()