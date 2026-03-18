# plan: Plot time series with rolling mean and confidence bands using multi_ts data
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    
    # Verify required columns exist
    if 'ts' not in df.columns or 'value' not in df.columns or 'metric' not in df.columns:
        result = {"summary": "Missing required columns.", "output_paths": [], "status": "no_data"}
    else:
        # Ensure timestamp is datetime
        df['ts'] = pd.to_datetime(df['ts'])
        
        # For each unique metric, create a subplot with confidence bands
        metrics = df['metric'].unique()
        fig, axs = plt.subplots(len(metrics), 1, figsize=(10, 4*len(metrics)), sharex=True)
        axs = np.atleast_1d(axs)
        
        for idx, metric in enumerate(metrics):
            metric_data = df[df['metric'] == metric].sort_values('ts')
            
            # Calculate rolling statistics
            window = 10
            rolling = metric_data['value'].rolling(window=window, center=True)
            mean = rolling.mean()
            std = rolling.std()
            
            # Plot
            ax = axs[idx]
            ax.plot(metric_data['ts'], mean, label='Rolling Mean', color='blue')
            ax.fill_between(metric_data['ts'], 
                          mean - 2*std, 
                          mean + 2*std, 
                          alpha=0.2, 
                          color='blue',
                          label='95% Confidence')
            ax.scatter(metric_data['ts'], metric_data['value'], 
                      alpha=0.2, color='gray', s=10, label='Raw Data')
            
            ax.set_title(f'{metric} Time Series')
            ax.set_ylabel('Value')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        axs[-1].set_xlabel('Time')
        fig.tight_layout()
        
        path = save_figure(fig, 
                         filename="timeseries_with_confidence.png",
                         summary="Time series with rolling mean and confidence bands")
        
        result = {
            "summary": f"Generated 1 figure with {len(metrics)} time series plots including confidence bands.",
            "output_paths": [path],
            "status": "ok"
        }