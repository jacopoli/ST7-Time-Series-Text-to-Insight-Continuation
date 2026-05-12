# plan: Plot temperature vs time for each site using different colors on a single plot

keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('multi_site')
    
    # Create the figure and plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each site with a different color
    sites = df['site'].unique()
    for site in sites:
        site_data = df[df['site'] == site]
        ax.plot(site_data['datetime'], site_data['temperature'], label=site)
    
    # Customize the plot
    ax.set_title('Temperature Comparison Across Sites')
    ax.set_xlabel('Date/Time')
    ax.set_ylabel('Temperature')
    ax.legend(title='Site')
    ax.grid(True, alpha=0.3)
    
    # Save the figure
    path = save_figure(fig, 
                      filename="multi_site_temperature.png",
                      summary="Temperature trends comparison across all sites")
    
    result = {
        "summary": f"Generated 1 chart comparing temperature trends across {len(sites)} sites.",
        "output_paths": [path],
        "status": "ok"
    }