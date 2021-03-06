# vim: fdm=indent
'''
author:     Fabio Zanini
date:       15/06/15
content:    Make figure 2 and figure S10.
            This script plots precomputed data, so you have to run it after the
            following scripts that actually compute the results:
               - fitness_cost_saturation.py (sat fit)
               - fitness_cost_KL.py (KL fit)
               - combined_af.py (pooled fit)
'''
# Modules
import os
import sys
import argparse
from itertools import izip
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from Bio.Seq import translate

from hivevo.patients import Patient
from hivevo.HIVreference import HIVreference
from hivevo.sequence import alpha, alphal

from util import add_binned_column, boot_strap_patients



# Functions
def load_data_saturation():
    import cPickle as pickle
    fn = '../data/fitness_saturation/fitness_cost_saturation_plot.pickle'
    with open(fn, 'r') as f:
        data = pickle.load(f)

    fn = '../data/fitness_saturation/fitness_cost_data_nosweep_Sbins.npz'
    with np.load(fn) as bin_file:
        bins = bin_file['bins']

    return data, bins


def load_data_KL():
    '''Load data from Vadim's KL approach'''
    S_center = np.loadtxt('../data/fitness_KL/genomewide_smuD_KL_quant_medians.txt')
    s_mean, s_std = np.loadtxt('../data/fitness_KL/genomewide_smuD_KLmu_multi_boot.txt')[:,:-2]

    data = pd.DataFrame({'mean': s_mean, 'std': s_std}, index=S_center)
    data.index.name = 'Entropy'
    data.name = 'fitness costs'

    return data


def load_data_pooled(avg='harmonic'):
    '''Load data from the pooled allele frequencies'''
    import cPickle as pickle
    with open('../data/fitness_pooled/pooled_'+avg+'_selection_coeff_st_any.pkl', 'r') as f:
        caf_s = pickle.load(f)
    return caf_s


def plot_fit(data_sat, data_pooled, bins_sat):
    from matplotlib import cm
    from util import add_panel_label

    palette = sns.color_palette('colorblind')

    fig_width = 5
    fs = 16
    fig, axs = plt.subplots(1, 2,
                            figsize=(2 * fig_width, fig_width))


    data_to_fit = data_sat['data_to_fit']
    mu = data_sat['mu']
    s = data_sat['s']

    fun = lambda x, s: mu / s * (1.0 - np.exp(-s * x))

    # PANEL A: data and fits
    ax = axs[0]
    for iS, (S, datum) in enumerate(data_to_fit.iterrows()):
        x = np.array(datum.index)
        y = np.array(datum)
        color = cm.jet(1.0 * iS / data_to_fit.shape[0])

        # Most conserved group is dashed
        if iS == 0:
            ls = '--'
        else:
            ls = '-'

        ax.scatter(x, y,
                   s=70,
                   color=color,
                  )

        xfit = np.linspace(0, 3000)
        yfit = fun(xfit, s.loc[S, 's'])
        ax.plot(xfit, yfit,
                lw=2,
                color=color,
                ls=ls,
               )

    ax.set_xlabel('days since EDI', fontsize=fs)
    ax.set_ylabel('divergence', fontsize=fs)
    ax.set_xlim(-200, 3200)
    ax.set_ylim(-0.0005, 0.025)
    ax.set_xticks(np.linspace(0, 0.005, 5))
    ax.set_xticks([0, 1000, 2000, 3000])
    ax.xaxis.set_tick_params(labelsize=fs)
    ax.yaxis.set_tick_params(labelsize=fs)

    ax.text(0, 0.023,
            r'$\mu = 1.2 \cdot 10^{-5}$ per day',
            fontsize=16)
    ax.plot([200, 1300], [0.007, 0.007 + (1300 - 200) * mu], lw=1.5, c='k')

    # PANEL B: costs
    ax = axs[1]

    # B1: Saturation fit
    x = np.array(s.index)
    y = np.array(s['s'])
    dy = np.array(s['ds'])

    ymin = 0.1

    x = x[1:]
    y = y[1:]
    dx = np.array((x-bins_sat[1:-1], bins_sat[2:]-x))
    dy = dy[1:]
    ax.errorbar(x, y,
                yerr=dy,
                xerr=dx,
                ls='-',
                marker='o',
                lw=2,
                color=palette[0],
                label='Sat',
               )

    # Annotate with colors from panel A
    #ax.scatter(x, y,
    #           marker='o',
    #           s=130,
    #           edgecolor=cm.jet(1.0 * np.arange(1, data_to_fit.shape[0]) / data_to_fit.shape[0]),
    #           facecolor='none',
    #           lw=2,
    #           zorder=5,
    #           )
    for iS in xrange(1, data_to_fit.shape[0]):
        ax.annotate('',
                    xy=(x[iS - 1],
                        y[iS - 1] * 0.7 if iS != data_to_fit.shape[0] - 1 else 1e-4),
                    xytext=(x[iS - 1],
                            y[iS - 1] * 1.0 / 3 if iS != data_to_fit.shape[0] - 1 else 2e-4),
                    arrowprops={'facecolor': cm.jet(1.0 * iS / data_to_fit.shape[0]),
                                'edgecolor': 'none',
                                'shrink': 0.05},
                    )

    # B2: pooled
    x = data_pooled['all'][:-1, 0]
    y = data_pooled['all'][:-1, -1]
    dy = data_pooled['all_std'][:-1, -1]
    dx = np.array((x-data_pooled['all'][:-1, 1], data_pooled['all'][:-1, 2]-x))
    ax.errorbar(x, y, yerr=dy, xerr=dx,
                ls='-',
                marker='o',
                lw=2,
                color=palette[2],
                label='Pooled',
               )

    ax.legend(loc='upper right', fontsize=16)
    ax.set_xlabel('variability in group M [bits]', fontsize=fs)
    ax.set_ylabel('fitness cost [1/day]', fontsize=fs)
    ax.set_xlim(0.9e-3, 2.5)
    ax.set_ylim(9e-5, 0.11)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.xaxis.set_tick_params(labelsize=fs)
    ax.yaxis.set_tick_params(labelsize=fs)


    # Panel labels
    add_panel_label(axs[0], 'A', x_offset=-0.27)
    add_panel_label(axs[1], 'B', x_offset=-0.21)

    plt.tight_layout()
    plt.ion()
    plt.show()


def plot_fit_withKL(data_sat, data_KL, data_pooled, bins_sat):
    from matplotlib import cm
    from util import add_panel_label

    palette = sns.color_palette('colorblind')

    fig_width = 6
    fs = 16
    fig, ax = plt.subplots(1, 1,
                           figsize=(fig_width, 0.9 * fig_width))

    data_to_fit = data_sat['data_to_fit']
    mu = data_sat['mu']
    s = data_sat['s']

    # B1: Saturation fit
    ymin = 0.1

    x = np.array(s.index)
    y = np.array(s['s'])
    dy = np.array(s['ds'])
    dx = np.array((x-bins_sat[:-1], bins_sat[1:]-x))
    x = x[1:]
    y = y[1:]
    dy = dy[1:]
    dx = dx[:, 1:]

    ax.errorbar(x, y,
                yerr=dy,
                xerr=dx,
                ls='-',
                marker='o',
                lw=2,
                color=palette[0],
                label='Sat',
               )

    # B2: KL fit
    # Ignore most conserved quantile
    x = np.array(data_KL.index)
    y = np.array(data_KL['mean'])
    dy = np.array(data_KL['std'])
    dx = np.array((x-bins_sat[1:-1], bins_sat[2:]-x))
    x = x[1:]
    y = y[1:]
    dy = dy[1:]
    dx = dx[:, 1:]

    ax.errorbar(x, y, yerr=dy, xerr=dx,
                ls='-',
                marker='o',
                lw=2,
                color=palette[1],
                label='KL',
               )

    # B3: pooled
    for avg, d in data_pooled.iteritems():
        x = d['all'][:-1, 0]
        y = d['all'][:-1, -1]
        dy = d['all_std'][:-1, 1]
        dx = np.array((x-d['all'][:-1, 1], d['all'][:-1, 2]-x))

        if avg == 'arithmetic':
            color = '#aad400'
        else:
            color = palette[2]

        ax.errorbar(x, y, yerr=dy, xerr=dx,
                    ls='-',
                    marker='o',
                    lw=2,
                    color=color,
                    label='Pooled - '+avg +' mean',
                   )

    ax.legend(loc='lower left', fontsize=fs*0.8)
    ax.set_xlabel('variability in group M [bits]', fontsize=fs)
    ax.set_ylabel('fitness cost [1/day]', fontsize=fs)
    ax.set_xlim(0.9e-3, 2.5)
    ax.set_ylim(9e-5, 0.11)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.xaxis.set_tick_params(labelsize=fs*0.8)
    ax.yaxis.set_tick_params(labelsize=fs*0.8)


    plt.tight_layout()
    plt.ion()
    plt.show()




# Script
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Figure 2')
    parser.add_argument('--KL', action='store_true',
                        help='include KL estimates')
    parser.add_argument('--all', action='store_true',
                        help='include geometric and arithmetic average')
    args = parser.parse_args()

    data_sat, bins_sat = load_data_saturation()
    data_pooled = load_data_pooled()

    plot_fit(data_sat, data_pooled, bins_sat)

    for ext in ['png', 'pdf', 'svg']:
        plt.savefig('../figures/figure_2'+'.'+ext)

    if args.KL:
        data_KL = load_data_KL()
        if args.all:
            data_pooled = {avg:load_data_pooled(avg=avg)
                        for avg in ['harmonic', 'arithmetic']}
        else:
            data_pooled = {avg:load_data_pooled(avg=avg)
                        for avg in ['harmonic']}

        plot_fit_withKL(data_sat, data_KL, data_pooled, bins_sat)
        for ext in ['png', 'pdf', 'svg']:
            plt.savefig('../figures/figure_S10'+'.'+ext)
