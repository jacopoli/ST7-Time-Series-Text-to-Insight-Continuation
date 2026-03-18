# plan: Create histogram from categorical dataset showing distribution of counts by category
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('categorical')
    
    if 'category' not in df.columns or 'count' not in df.columns:
        result = {"summary": "Missing required category or count columns.", "output_paths": [], "status": "no_data"}
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create bar plot of counts by category
        categories = df.groupby('category')['count'].sum().sort_values(ascending=False)
        
        ax.bar(categories.index, categories.values)
        ax.set_title('Distribution of Counts by Category')
        ax.set_xlabel('Category')
        ax.set_ylabel('Total Count')
        
        # Rotate x-axis labels if there are many categories
        if len(categories) > 6:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        path = save_figure(fig, filename="category-distribution.png", 
                         summary="Distribution of counts across categories")
        
        result = {
            "summary": f"Generated 1 histogram showing category distribution from {keys[0]}.",
            "output_paths": [path],
            "status": "ok"
        }