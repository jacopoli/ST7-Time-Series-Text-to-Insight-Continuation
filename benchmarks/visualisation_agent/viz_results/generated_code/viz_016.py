# plan: Create manual time series decomposition visualization using rolling means and differences
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('simple_ts')
    
    # Calculate trend using rolling mean
    window = 10  # Period for decomposition
    df['trend'] = df['value'].rolling(window=window, center=True).mean()
    
    # Calculate detrended (roughly seasonal + residual)
    df['detrended'] = df['value'] - df['trend']
    
    # Estimate seasonal pattern (average by position in cycle)
    df['position'] = np.arange(len(df)) % window
    seasonal_pattern = df.groupby('position')['detrended'].mean()
    df['seasonal'] = [seasonal_pattern[pos] for pos in df['position']]
    
    # Calculate residual
    df['residual'] = df['detrended'] - df['seasonal']
    
    # Create subplots
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 12))
    
    # Original data
    ax1.plot(df['ts'], df['value'])
    ax1.set_title('Original Time Series')
    ax1.set_ylabel('Value')
    
    # Trend
    ax2.plot(df['ts'], df['trend'])
    ax2.set_title(f'Trend (Rolling Mean, window={window})')
    ax2.set_ylabel('Value')
    
    # Seasonal
    ax3.plot(df['ts'], df['seasonal'])
    ax3.set_title('Seasonal Pattern')
    ax3.set_ylabel('Value')
    
    # Residual
    ax4.plot(df['ts'], df['residual'])
    ax4.set_title('Residual')
    ax4.set_ylabel('Value')
    ax4.set_xlabel('Time')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    path = save_figure(fig, filename='time_series_decomposition.png', 
                      summary='Time series decomposition showing original, trend, seasonal, and residual components')
    
    result = {
        "summary": f"Generated time series decomposition plot from {keys[0]}",
        "output_paths": [path],
        "status": "ok"
    }