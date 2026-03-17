# plan: Create scatter plot from measurements dataset, with time on x-axis, reading on y-axis, color by channel
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    if "time" not in df.columns or "reading" not in df.columns or "channel" not in df.columns:
        result = {"summary": "Missing required columns for scatter plot.", "output_paths": [], "status": "no_data"}
    else:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["time", "reading"])
        
        # Create scatter plot with different colors per channel
        fig, ax = plt.subplots(figsize=(10, 6))
        channels = df["channel"].unique()
        for channel in channels:
            mask = df["channel"] == channel
            ax.scatter(df.loc[mask, "time"], df.loc[mask, "reading"], 
                      label=channel, alpha=0.6, s=30)
        
        ax.set_xlabel("Time")
        ax.set_ylabel("Reading")
        ax.set_title("Measurements by Channel Over Time")
        ax.legend(title="Channel")
        ax.grid(True, alpha=0.3)
        
        path = save_figure(fig, filename="measurements-scatter.png", 
                         summary="Scatter plot of readings by channel over time")
        result = {
            "summary": f"Generated 1 scatter plot from {keys[0]}.",
            "output_paths": [path],
            "status": "ok"
        }