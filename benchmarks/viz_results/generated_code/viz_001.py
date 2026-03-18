# plan: Create a basic line chart using the simple time series data
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("simple_ts")
    
    # Create simple line plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['ts'], df['value'], label='Value')
    
    # Customize the plot
    ax.set_title('Time Series Data')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Value')
    ax.grid(True)
    ax.legend()
    
    # Save the figure
    path = save_figure(fig, filename="simple_timeseries.png", 
                      summary="Simple time series line plot")
    
    result = {
        "summary": "Generated 1 line chart from simple_ts dataset.",
        "output_paths": [path],
        "status": "ok"
    }