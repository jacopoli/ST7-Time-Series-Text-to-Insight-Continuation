# plan: Create a heatmap of temperature readings across sites and time using multi_site dataset
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("multi_site")
    if "datetime" not in df.columns or "site" not in df.columns or "temperature" not in df.columns:
        result = {"summary": "Missing required columns for heatmap.", "output_paths": [], "status": "no_data"}
    else:
        # Pivot the data to create a matrix of sites x time
        pivot_df = df.pivot(index='site', columns='datetime', values='temperature')
        
        # Create the heatmap
        fig, ax = plt.subplots(figsize=(12, 6))
        im = ax.imshow(pivot_df, aspect='auto', cmap='viridis')
        
        # Customize the plot
        plt.colorbar(im, label='Temperature')
        ax.set_title('Temperature Heatmap by Site')
        
        # Format x-axis (time) - use numeric indices and format simple dates
        x_ticks = range(0, len(pivot_df.columns), len(pivot_df.columns)//6)
        ax.set_xticks(x_ticks)
        x_labels = [pd.Timestamp(pivot_df.columns[i]).strftime('%m-%d') for i in x_ticks]
        ax.set_xticklabels(x_labels, rotation=45)
        
        # Format y-axis (sites)
        ax.set_yticks(range(len(pivot_df.index)))
        ax.set_yticklabels(pivot_df.index)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        path = save_figure(fig, filename="temperature-heatmap.png", 
                         summary="Heatmap showing temperature variation across sites and time")
        
        result = {
            "summary": "Generated temperature heatmap from multi_site data.",
            "output_paths": [path],
            "status": "ok"
        }