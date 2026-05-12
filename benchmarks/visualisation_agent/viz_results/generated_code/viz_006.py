# plan: Use multi_ts dataset to create separate subplots for each metric type

keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("multi_ts")
    
    # Verify required columns exist
    if not all(col in df.columns for col in ["ts", "metric", "value"]):
        result = {"summary": "Missing required columns in dataset.", "output_paths": [], "status": "no_data"}
    else:
        # Ensure timestamp is datetime
        df["ts"] = pd.to_datetime(df["ts"])
        
        # Get unique metrics
        metrics = df["metric"].unique()
        
        # Create subplots, one for each metric
        fig, axs = plt.subplots(len(metrics), 1, figsize=(10, 3*len(metrics)), sharex=True)
        axes = np.atleast_1d(axs)
        
        # Plot each metric in its own subplot
        for idx, metric in enumerate(metrics):
            metric_data = df[df["metric"] == metric]
            axes[idx].plot(metric_data["ts"], metric_data["value"], label=metric)
            axes[idx].set_title(f"{metric} Over Time")
            axes[idx].set_ylabel("Value")
            axes[idx].grid(True)
            axes[idx].legend()
        
        # Set common x-axis label
        axes[-1].set_xlabel("Time")
        
        # Add overall title
        fig.suptitle("Sensor Metrics Time Series")
        
        # Adjust layout to prevent overlap
        plt.tight_layout()
        
        # Save the figure
        path = save_figure(fig, filename="sensor_metrics_subplots.png", 
                         summary="Time series subplots for multiple sensor metrics")
        
        result = {
            "summary": f"Generated 1 figure with {len(metrics)} subplots from multi_ts dataset",
            "output_paths": [path],
            "status": "ok"
        }