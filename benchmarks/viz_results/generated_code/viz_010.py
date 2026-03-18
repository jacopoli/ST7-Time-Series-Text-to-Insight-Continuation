# plan: Create line chart showing temperature trends for different sites over time
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('multi_site')
    
    # Ensure datetime is properly parsed
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Get unique sites and assign different colors
    sites = df['site'].unique()
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    
    # Plot each site's temperature
    for idx, site in enumerate(sites):
        site_data = df[df['site'] == site]
        ax1.plot(site_data['datetime'], site_data['temperature'], 
                label=site, color=colors[idx % len(colors)])
    
    # Customize primary axis
    ax1.set_xlabel('Date/Time')
    ax1.set_ylabel('Temperature')
    ax1.tick_params(axis='y')
    
    # Add legend and title
    ax1.legend(loc='upper left')
    plt.title('Temperature Trends by Site')
    
    # Adjust layout and save
    plt.tight_layout()
    path = save_figure(fig, filename="temperature_trends.png", 
                      summary="Temperature trends across multiple sites")
    
    result = {
        "summary": f"Generated temperature trend visualization from {keys[0]}",
        "output_paths": [path],
        "status": "ok"
    }