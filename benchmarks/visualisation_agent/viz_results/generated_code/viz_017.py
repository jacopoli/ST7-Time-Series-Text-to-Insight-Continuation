# plan: Create cumulative distribution plot of readings, one line per channel from measurements dataset.
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    channels = df['channel'].unique()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot CDF for each channel
    for channel in channels:
        channel_data = df[df['channel'] == channel]['reading'].sort_values()
        n = len(channel_data)
        cumulative_prob = np.arange(1, n + 1) / n
        ax.plot(channel_data, cumulative_prob, label=f'Channel {channel}', alpha=0.7)
    
    ax.set_xlabel('Reading Value')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('Cumulative Distribution of Measurements by Channel')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    path = save_figure(fig, filename="measurements-cdf.png", 
                      summary="Cumulative distribution plot of measurement readings by channel.")
    
    result = {
        "summary": f"Generated CDF plot from {keys[0]} showing distribution across {len(channels)} channels.",
        "output_paths": [path],
        "status": "ok"
    }