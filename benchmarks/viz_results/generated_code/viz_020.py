# plan: Create faceted time series plots from multi_ts and multi_site datasets

# Part 1: Handle multi_ts long-form data with metrics as series
paths = []
df = get_df('multi_ts')

# Pivot long to wide format for plotting
wide_df = df.pivot(index='ts', columns='metric', values='value').reset_index()

# Get unique metrics for plotting
metrics = df['metric'].unique().tolist()

# Create figure with subplots (max 2 metrics per subplot)
pairs = [metrics[i:i+2] for i in range(0, len(metrics), 2)]
fig, axes = plt.subplots(len(pairs), 1, figsize=(12, 4*len(pairs)), sharex=True)
axes = np.atleast_1d(axes)

# Plot each pair of metrics
for idx, (ax, metric_pair) in enumerate(zip(axes, pairs)):
    # First metric on left y-axis
    ax.plot(wide_df['ts'], wide_df[metric_pair[0]], 
            color='tab:blue', label=metric_pair[0])
    ax.set_ylabel(metric_pair[0], color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    
    # Second metric on right y-axis if it exists
    if len(metric_pair) > 1:
        ax2 = ax.twinx()
        ax2.plot(wide_df['ts'], wide_df[metric_pair[1]], 
                color='tab:orange', label=metric_pair[1])
        ax2.set_ylabel(metric_pair[1], color='tab:orange')
        ax2.tick_params(axis='y', labelcolor='tab:orange')
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    else:
        ax.legend(loc='upper right')

    ax.grid(True, alpha=0.3)
    
axes[-1].set_xlabel('Time')
fig.suptitle('Time Series by Metric (multi_ts)')
fig.tight_layout()
paths.append(save_figure(fig, filename='multi_ts_metrics.png', 
                        summary='Multi-metric time series from multi_ts'))

# Part 2: Handle multi_site data with sites as series
df_site = get_df('multi_site')
sites = df_site['site'].unique()

# Create figure with one subplot per site
fig, axes = plt.subplots(len(sites), 1, figsize=(12, 4*len(sites)), sharex=True)
axes = np.atleast_1d(axes)

for ax, site in zip(axes, sites):
    site_data = df_site[df_site['site'] == site]
    ax.plot(site_data['datetime'], site_data['temperature'], 
            label=f'Site {site}')
    ax.set_ylabel('Temperature')
    ax.set_title(f'Site {site}')
    ax.grid(True, alpha=0.3)
    ax.legend()

axes[-1].set_xlabel('Time')
fig.suptitle('Temperature by Site (multi_site)')
fig.tight_layout()
paths.append(save_figure(fig, filename='multi_site_temps.png', 
                        summary='Temperature time series by site'))

result = {
    "summary": f"Generated {len(paths)} figures from multi_ts and multi_site datasets",
    "output_paths": paths,
    "status": "ok"
}