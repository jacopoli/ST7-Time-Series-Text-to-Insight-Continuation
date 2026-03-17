# plan: Create a grouped bar chart comparing min/mean/max statistics using the statistics dataset
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("statistics")
    
    # Check required columns exist
    if "type" not in df.columns or "value" not in df.columns:
        result = {"summary": "Missing required type or value columns.", "output_paths": [], "status": "no_data"}
    else:
        # Pivot the data to get statistics side by side
        pivoted = df.pivot(columns="type", values="value")
        
        # Create the grouped bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(3)  # Three groups for min, mean, max
        width = 0.25  # Width of bars
        
        stats = ["min", "mean", "max"]
        metrics = pivoted.columns.unique()
        
        for i, metric in enumerate(metrics):
            values = [
                pivoted[metric].min(),
                pivoted[metric].mean(),
                pivoted[metric].max()
            ]
            ax.bar(x + i*width, values, width, label=metric)
        
        ax.set_ylabel('Value')
        ax.set_title('Statistics Comparison by Type')
        ax.set_xticks(x + width)
        ax.set_xticklabels(stats)
        ax.legend()
        
        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        path = save_figure(fig, filename="statistics-comparison.png", 
                         summary="Grouped bar chart comparing min/mean/max statistics by type.")
        
        result = {
            "summary": f"Generated 1 chart from statistics dataset showing min/mean/max comparison.",
            "output_paths": [path],
            "status": "ok"
        }