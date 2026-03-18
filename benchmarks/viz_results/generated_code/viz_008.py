# plan: Create visualization showing available data points and gaps in time series
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    time_col = "ts" if "ts" in df.columns else "timestamp" if "timestamp" in df.columns else None
    value_col = "value" if "value" in df.columns else None
    
    if not time_col or not value_col:
        result = {"summary": "Missing required time or value columns.", "output_paths": [], "status": "no_data"}
    else:
        # Convert time and ensure it's sorted
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        df = df.sort_values(time_col)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[3, 1])
        
        # Plot 1: Main time series with gaps
        ax1.plot(df[time_col], df[value_col], 'b-', label='Available data')
        ax1.scatter(df[time_col][df[value_col].isna()], 
                   [df[value_col].mean()] * df[value_col].isna().sum(), 
                   color='red', marker='x', label='Missing values')
        ax1.set_title('Time Series with Missing Values')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Value')
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Data availability heatmap
        available = df[value_col].notna()
        ax2.scatter(df[time_col][available], [1] * available.sum(), 
                   marker='s', s=100, c='green', label='Available')
        ax2.scatter(df[time_col][~available], [1] * (~available).sum(), 
                   marker='s', s=100, c='red', label='Missing')
        ax2.set_title('Data Availability')
        ax2.set_yticks([])
        ax2.set_xlabel('Time')
        ax2.legend()
        
        # Add stats in text
        total_points = len(df)
        missing_points = df[value_col].isna().sum()
        available_points = total_points - missing_points
        stats_text = (f'Total points: {total_points}\n'
                     f'Available: {available_points} ({available_points/total_points*100:.1f}%)\n'
                     f'Missing: {missing_points} ({missing_points/total_points*100:.1f}%)')
        fig.text(0.02, 0.02, stats_text, fontsize=8)
        
        plt.tight_layout()
        path = save_figure(fig, filename="missing_values_analysis.png", 
                         summary="Time series visualization with missing value analysis")
        
        result = {
            "summary": f"Generated missing value analysis chart from {keys[0]}",
            "output_paths": [path],
            "status": "ok"
        }