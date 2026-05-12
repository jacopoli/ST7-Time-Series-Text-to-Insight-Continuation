# plan: Create boxplot showing reading distribution by channel from measurements dataset
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    if "channel" not in df.columns or "reading" not in df.columns:
        result = {"summary": "Missing required channel/reading columns.", "output_paths": [], "status": "no_data"}
    else:
        # Create figure with reasonable size based on number of channels
        n_channels = df["channel"].nunique()
        fig_width = max(8, min(12, n_channels * 0.8))
        fig, ax = plt.subplots(figsize=(fig_width, 6))
        
        # Create boxplot
        boxplot = df.boxplot(column="reading", by="channel", ax=ax)
        
        # Customize appearance
        ax.set_title("Distribution of Measurements by Channel")
        ax.set_xlabel("Channel")
        ax.set_ylabel("Reading Value")
        
        # Rotate x-axis labels if there are many channels
        if n_channels > 8:
            plt.xticks(rotation=45, ha="right")
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        path = save_figure(fig, filename="measurement-distributions.png", 
                         summary="Boxplot showing measurement distributions across channels")
        
        result = {
            "summary": f"Generated 1 boxplot from {keys[0]} showing distributions across {n_channels} channels.",
            "output_paths": [path],
            "status": "ok"
        }