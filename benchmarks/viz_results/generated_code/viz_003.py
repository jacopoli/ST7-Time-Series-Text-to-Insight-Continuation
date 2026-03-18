# plan: Create scatter plot of measurements per channel over time
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    
    # Check required columns exist
    if 'time' not in df.columns or 'channel' not in df.columns or 'reading' not in df.columns:
        result = {"summary": "Missing required columns.", "output_paths": [], "status": "no_data"}
    else:
        # Convert time to datetime if needed
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        
        # Get unique channels
        channels = df['channel'].unique()
        
        # Create scatter plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot each channel with different color/marker
        for channel in channels:
            channel_data = df[df['channel'] == channel]
            ax.scatter(channel_data['time'], channel_data['reading'], 
                      label=str(channel), alpha=0.6, s=30)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Reading')
        ax.set_title('Measurements by Channel')
        ax.legend(title='Channel', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        path = save_figure(fig, filename="measurements_scatter.png", 
                         summary="Scatter plot of measurements by channel over time")
        
        result = {
            "summary": f"Generated scatter plot from {keys[0]} showing {len(channels)} channels.",
            "output_paths": [path],
            "status": "ok"
        }