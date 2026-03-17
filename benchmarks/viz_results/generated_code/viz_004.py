# plan: Create subplots for wide_metrics dataset, 2 metrics per subplot with twinx axes
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    time_col = "date"
    metric_cols = ["metric_a", "metric_b", "metric_c"]
    
    if not all(col in df.columns for col in [time_col] + metric_cols):
        result = {"summary": "Missing required columns.", "output_paths": [], "status": "no_data"}
    else:
        # Convert time column to datetime if needed
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col])
        
        # Split metrics into pairs for subplots (2 per subplot max)
        pairs = [metric_cols[i:i+2] for i in range(0, len(metric_cols), 2)]
        
        # Create figure with subplots
        fig, axs = plt.subplots(len(pairs), 1, sharex=True, figsize=(10, 3*len(pairs)))
        axes = np.atleast_1d(axs)
        
        for ax, pair in zip(axes, pairs):
            # Plot first metric on left axis
            ax.plot(df[time_col], df[pair[0]], color='tab:blue', label=pair[0])
            ax.set_ylabel(pair[0], color='tab:blue')
            ax.tick_params(axis='y', labelcolor='tab:blue')
            
            lines, labels = ax.get_legend_handles_labels()
            
            # Plot second metric on right axis if it exists
            if len(pair) > 1:
                ax2 = ax.twinx()
                ax2.plot(df[time_col], df[pair[1]], color='tab:orange', label=pair[1])
                ax2.set_ylabel(pair[1], color='tab:orange')
                ax2.tick_params(axis='y', labelcolor='tab:orange')
                # Offset the right spine
                ax2.spines['right'].set_position(('axes', 1.1))
                
                line2, label2 = ax2.get_legend_handles_labels()
                lines += line2
                labels += label2
            
            ax.grid(True, alpha=0.3)
            ax.legend(lines, labels, loc='upper left', bbox_to_anchor=(0, 1.15))
        
        # Set common x-axis label and title
        axes[-1].set_xlabel('Date')
        fig.suptitle('Multiple Metrics Over Time')
        
        # Adjust layout to prevent overlapping
        plt.tight_layout()
        
        path = save_figure(fig, filename="multiple_metrics.png", 
                         summary="Multiple metrics plotted with separate y-axes")
        
        result = {
            "summary": f"Generated 1 figure with {len(pairs)} subplots from {keys[0]}.",
            "output_paths": [path],
            "status": "ok"
        }