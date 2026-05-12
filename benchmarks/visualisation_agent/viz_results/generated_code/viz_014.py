# plan: Plot sparse time series data, highlighting gaps in measurements.

keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    time_col = "ts" if "ts" in df.columns else "timestamp" if "timestamp" in df.columns else None
    value_col = "value" if "value" in df.columns else None
    
    if not time_col or not value_col:
        result = {"summary": "Missing time or value columns.", "output_paths": [], "status": "no_data"}
    else:
        # Ensure datetime
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        
        # Sort by time and reset index
        df = df.sort_values(time_col).reset_index(drop=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plot actual measurements with dots
        ax.scatter(df[time_col], df[value_col], label='Measurements', 
                  color='blue', alpha=0.6, s=30)
        
        # Connect measurements with lines
        ax.plot(df[time_col], df[value_col], color='lightblue', 
                alpha=0.3, linestyle='--', label='Connections')
        
        # Customize the plot
        ax.set_title('Time Series with Missing Periods')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add text about data points
        total_points = len(df)
        total_duration = df[time_col].max() - df[time_col].min()
        ax.text(0.02, 0.98, 
                f'Total points: {total_points}\nTime span: {total_duration}',
                transform=ax.transAxes, 
                verticalalignment='top',
                bbox=dict(facecolor='white', alpha=0.8))
        
        path = save_figure(fig, filename="sparse_timeseries.png", 
                         summary="Time series visualization showing gaps in measurements")
        
        result = {
            "summary": f"Generated 1 chart from {keys[0]} showing sparse time series data.",
            "output_paths": [path],
            "status": "ok"
        }