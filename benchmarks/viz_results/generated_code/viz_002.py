# plan: Use categorical dataset to create a bar chart showing count by category
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("categorical") if "categorical" in keys else get_df(keys[0])
    if "category" not in df.columns or "count" not in df.columns:
        result = {"summary": "Missing required category/count columns.", "output_paths": [], "status": "no_data"}
    else:
        # Aggregate total counts per category
        agg = df.groupby("category")["count"].sum().sort_values(ascending=True)
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        agg.plot(kind="barh", ax=ax)
        
        ax.set_title("Total Count by Category")
        ax.set_xlabel("Total Count")
        ax.set_ylabel("Category")
        
        # Add value labels on the bars
        for i, v in enumerate(agg):
            ax.text(v, i, f" {v:,}", va="center")
        
        path = save_figure(fig, filename="category-counts.png", 
                         summary="Horizontal bar chart showing total counts per category")
        
        result = {
            "summary": f"Generated 1 bar chart from {keys[0]} showing counts across {len(agg)} categories.",
            "output_paths": [path],
            "status": "ok"
        }