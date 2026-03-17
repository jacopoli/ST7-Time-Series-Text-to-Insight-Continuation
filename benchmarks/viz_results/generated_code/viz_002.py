# plan: Create a bar chart using the categorical dataset, showing count by category

keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df(keys[0])
    if "category" not in df.columns or "count" not in df.columns:
        result = {"summary": "Missing required category or count columns.", "output_paths": [], "status": "no_data"}
    else:
        # Aggregate counts by category if needed
        plot_df = df.groupby("category")["count"].sum().reset_index()
        
        # Sort by count descending for better visualization
        plot_df = plot_df.sort_values("count", ascending=False)
        
        # Create the bar chart
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(plot_df["category"], plot_df["count"])
        
        # Customize the plot
        ax.set_title("Count by Category")
        ax.set_xlabel("Category")
        ax.set_ylabel("Count")
        
        # Rotate x-axis labels if there are many categories
        if len(plot_df) > 6:
            plt.xticks(rotation=45, ha='right')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        path = save_figure(fig, filename="category-counts.png", summary="Bar chart of counts by category")
        result = {
            "summary": f"Generated 1 bar chart from {keys[0]}",
            "output_paths": [path],
            "status": "ok"
        }