# plan: Create three-line plot with shared x-axis and split y-axes for metric_a, metric_b, metric_c
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    time_col = "date"
    metric_cols = ["metric_a", "metric_b", "metric_c"]
    
    # Validate required columns exist
    if not all(col in df.columns for col in [time_col] + metric_cols):
        result = {"summary": "Missing required columns.", "output_paths": [], "status": "no_data"}
    else:
        # Create figure with primary and two secondary y-axes
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot first metric on primary y-axis
        color1 = 'tab:blue'
        ax.plot(df[time_col], df[metric_cols[0]], color=color1, label=metric_cols[0])
        ax.set_ylabel(metric_cols[0], color=color1)
        ax.tick_params(axis='y', labelcolor=color1)
        
        # Create first secondary y-axis for second metric
        ax2 = ax.twinx()
        color2 = 'tab:orange'
        ax2.spines['right'].set_position(('outward', 60))
        ax2.plot(df[time_col], df[metric_cols[1]], color=color2, label=metric_cols[1])
        ax2.set_ylabel(metric_cols[1], color=color2)
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Create second secondary y-axis for third metric
        ax3 = ax.twinx()
        color3 = 'tab:green'
        ax3.spines['right'].set_position(('outward', 120))
        ax3.plot(df[time_col], df[metric_cols[2]], color=color3, label=metric_cols[2])
        ax3.set_ylabel(metric_cols[2], color=color3)
        ax3.tick_params(axis='y', labelcolor=color3)
        
        # Set title and x-axis label
        ax.set_title('Three Metrics Over Time')
        ax.set_xlabel('Date')
        
        # Combine legends from all axes
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, 
                 loc='upper left')
        
        # Adjust layout to prevent label overlap
        plt.tight_layout()
        
        # Save the figure
        path = save_figure(fig, filename="three_metrics.png", 
                         summary="Three metrics plotted over time with separate y-axes")
        
        result = {
            "summary": f"Generated 1 chart from {keys[0]} showing three metrics.",
            "output_paths": [path],
            "status": "ok"
        }