# plan: Create basic line chart from simple_ts dataset using ts and value columns
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df("simple_ts")
    
    # Create the line plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['ts'], df['value'], linewidth=2)
    
    # Customize the plot
    ax.set_title('Time Series Values')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Value')
    ax.grid(True)
    
    # Save the figure
    path = save_figure(fig, filename="simple_timeseries.png", 
                      summary="Simple time series line plot")
    
    result = {
        "summary": "Generated 1 line chart from simple_ts dataset.",
        "output_paths": [path],
        "status": "ok"
    }