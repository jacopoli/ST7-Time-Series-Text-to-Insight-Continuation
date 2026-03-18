# plan: Use statistics dataset to create a grouped bar chart comparing min/mean/max metrics.
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    # Load and validate data
    df = get_df("statistics") if "statistics" in keys else get_df(keys[0])
    
    # Check required columns exist
    if "type" not in df.columns or "value" not in df.columns:
        result = {"summary": "Missing required type/value columns.", "output_paths": [], "status": "no_data"}
    else:
        # Compute statistics for each type
        stats = df.groupby("type")["value"].agg(["min", "mean", "max"]).reset_index()
        
        # Set up the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate bar positions
        x = np.arange(len(stats))
        width = 0.25  # Width of bars
        
        # Create grouped bars
        ax.bar(x - width, stats["min"], width, label="Min", color="lightblue")
        ax.bar(x, stats["mean"], width, label="Mean", color="orange")
        ax.bar(x + width, stats["max"], width, label="Max", color="lightgreen")
        
        # Customize plot
        ax.set_title("Statistics Comparison by Type")
        ax.set_xlabel("Type")
        ax.set_ylabel("Value")
        ax.set_xticks(x)
        ax.set_xticklabels(stats["type"], rotation=45, ha="right")
        ax.legend()
        
        # Add grid for better readability
        ax.grid(True, axis="y", linestyle="--", alpha=0.7)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the figure
        path = save_figure(fig, filename="statistics-comparison.png", 
                         summary="Grouped bar chart comparing min/mean/max values by type")
        
        result = {
            "summary": f"Generated 1 grouped bar chart from statistics dataset.",
            "output_paths": [path],
            "status": "ok"
        }