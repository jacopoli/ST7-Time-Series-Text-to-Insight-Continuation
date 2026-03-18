# plan: Create violin plot of temperature distributions grouped by site from multi_site dataset
keys = list_datasets()
if not keys:
    result = {"summary": "No datasets available.", "output_paths": [], "status": "no_data"}
else:
    df = get_df('multi_site')
    if 'temperature' not in df.columns or 'site' not in df.columns:
        result = {"summary": "Missing required temperature or site columns.", "output_paths": [], "status": "no_data"}
    else:
        plt.figure(figsize=(10, 6))
        plt.violinplot([group['temperature'].values for name, group in df.groupby('site')],
                      positions=range(len(df['site'].unique())))
        plt.xticks(range(len(df['site'].unique())), df['site'].unique(), rotation=45)
        plt.title('Temperature Distribution by Site')
        plt.xlabel('Site')
        plt.ylabel('Temperature')
        plt.grid(True, alpha=0.3)
        
        # Add box plot inside violin plot for additional statistical information
        plt.boxplot([group['temperature'].values for name, group in df.groupby('site')],
                   positions=range(len(df['site'].unique())),
                   widths=0.1,
                   showfliers=False)
        
        plt.tight_layout()
        path = save_figure(plt.gcf(), filename="temp-distribution-by-site.png", 
                         summary="Violin plot showing temperature distribution across sites")
        result = {
            "summary": "Generated violin plot from multi_site dataset showing temperature distributions by site.",
            "output_paths": [path],
            "status": "ok"
        }