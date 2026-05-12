# plan: Create a 2x2 dashboard with both datasets. Use simple_ts for a line plot and rolling average,
# and wide_metrics for the remaining 3 subplots showing each metric's trends.

keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    # Load and prepare data
    df_simple = get_df('simple_ts')
    df_wide = get_df('wide_metrics')
    
    # Create 2x2 subplot layout
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Data Dashboard', fontsize=14, y=1.05)
    
    # Plot 1: Original and rolling average of simple_ts
    ax1 = axs[0, 0]
    df_simple['rolling_avg'] = df_simple['value'].rolling(window=5).mean()
    ax1.plot(df_simple['ts'], df_simple['value'], label='Raw', alpha=0.5)
    ax1.plot(df_simple['ts'], df_simple['rolling_avg'], label='5-point MA', linewidth=2)
    ax1.set_title('Time Series with Moving Average')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Value')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Metric A trend
    ax2 = axs[0, 1]
    ax2.plot(df_wide['date'], df_wide['metric_a'], color='tab:blue')
    ax2.set_title('Metric A Trend')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Metric A')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Metric B trend
    ax3 = axs[1, 0]
    ax3.plot(df_wide['date'], df_wide['metric_b'], color='tab:orange')
    ax3.set_title('Metric B Trend')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Metric B')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Metric C trend
    ax4 = axs[1, 1]
    ax4.plot(df_wide['date'], df_wide['metric_c'], color='tab:green')
    ax4.set_title('Metric C Trend')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Metric C')
    ax4.grid(True, alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the dashboard
    path = save_figure(fig, filename="dashboard.png", 
                      summary="Dashboard with 4 subplots showing time series and metrics trends")
    
    result = {
        "summary": f"Generated 1 dashboard figure using both datasets ({', '.join(keys)}).",
        "output_paths": [path],
        "status": "ok"
    }