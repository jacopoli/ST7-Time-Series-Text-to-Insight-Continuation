# plan: Create correlation heatmap for metric_a, metric_b, metric_c from wide_metrics dataset
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('wide_metrics')
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    
    if len(numeric_cols) < 2:
        result = {"summary": "Not enough numeric columns for correlation.", "output_paths": [], "status": "no_data"}
    else:
        # Compute correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Plot heatmap manually since seaborn is not available
        im = ax.imshow(corr_matrix, 
                      cmap='coolwarm',
                      vmin=-1, 
                      vmax=1)
        
        # Add correlation values as text
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                             ha='center', va='center',
                             color='white' if abs(corr_matrix.iloc[i, j]) > 0.5 else 'black')
        
        # Customize axes
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
        ax.set_yticklabels(numeric_cols)
        
        # Add colorbar
        plt.colorbar(im)
        
        plt.title('Correlation Matrix of Metrics')
        plt.tight_layout()
        
        # Save figure
        path = save_figure(fig, 
                          filename="correlation_matrix.png",
                          summary="Correlation heatmap of numeric metrics")
        
        result = {
            "summary": f"Generated correlation heatmap from {len(numeric_cols)} metrics in wide_metrics dataset.",
            "output_paths": [path],
            "status": "ok"
        }