from matplotlib import pyplot as plt
import numpy as np

def plot_stim(stim, stim_mark, stim_time, t_s_plot=None):

    if t_s_plot is None:
        t_s_plot = stim_time[::len(stim_time)//5]
    
    top_row = ''.join(list('ABCDEFGHIJ')[:len(t_s_plot)])
    bottom_row = 'T'*len(t_s_plot)

    fig, axs = plt.subplot_mosaic(
        f"""
        {top_row}
        {bottom_row}
        """,
        figsize=(12, 4),
    )

    h, w = stim.shape[1:3]
    for i, t_s in enumerate(t_s_plot):
        ax = axs[list('ABCDEFGHIJ')[i]]
        im = ax.imshow(stim[np.argmin(np.abs(stim_time - t_s))],
                       vmin=0, vmax=255, extent=(-w/2, w/2, h/2, -h/2), cmap='gray',
                       interpolation='None')
        plt.colorbar(im, ax=ax, ticks=[0, 255])
        ax.set(xlabel='left <-> right\n[pix=10 µm]', ylabel='front <-> back\n[pix=10 µm]', title=f't={t_s}s')

    ax = axs['T']
    center = stim[:, stim.shape[1]//2, stim.shape[2]//2]
    if stim.ndim == 4:
        for ch, color, name in zip(range(stim.shape[3]), ['r', 'g', 'b'], ['R', 'G', 'B']):
            ax.plot(stim_time, center[:, ch], color=color, label=f'{name} @ Center')
    else:
        ax.plot(stim_time, center, label='Int. @ Center')
    ax.vlines(stim_time[stim_mark], -70, -20, color='k', label='Trigger')
    ax.set(xlabel='Time [s]', ylabel='Intensity')
    ax.set_yticks((0, 100, 200, 255))
    tick_times = stim_time[stim_mark].astype(int)
    max_ticks = 15
    if len(tick_times) > max_ticks:
        step = int(np.ceil(len(tick_times) / max_ticks))
        tick_times = tick_times[::step]
    ax.set_xticks(tick_times)
    ax.legend(loc='upper right')

    plt.tight_layout()
    return fig, axs