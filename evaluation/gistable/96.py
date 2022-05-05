
import pandas as pd
import numpy as np

#setting up a comparable dataframe
df = pd.DataFrame(np.random.randint(20,100,size=(50, 4)), columns=['A','B','C','D'])
#these two columns become a multi-column index
df['year_idx'] = np.random.randint(2000,2004,50)
df['id_idx'] = np.random.randint(10000,19999,50)
df.drop_duplicates(subset=['year_idx','id_idx'],inplace=True)
df.set_index(['year_idx','id_idx'], inplace=True)
#add the year again as a normal column for easy access
df.loc[:,'year'] = df.index.get_level_values('year_idx')
#print(df)

#split out one of the years for separate analysis
#NOTE: THIS IS WHAT WAS GENERATING THE WARNING. NEEDED TO ADD .COPY() up here
#LOL after adding .loc everywhere because of the warning...
df_low = df.loc[(df['A'] < 90), :] #.copy()
df_high = df.loc[(df['A'] >= 90), :] #.copy()

#now going to group the values in column B into 5 bins and create a new column with the bin number
df_low['B_bin'] = pd.qcut(df_low['B'],5,labels=False)
#print(df)

#display the minimum value per bin
print('\nmin B value per bin:\n',df_low.groupby(['B_bin'])['B'].min())

#now want to do the same thing, but WANT THE BINS TO BE DETERMINED BY YEAR
for yr in df_low['year'].unique():
    #this works, but gives warning
    df_low.loc[df_low['year'] == yr,'B_bin_by_year'] = pd.qcut(df_low.loc[df_low['year'] == yr,'B'],8,labels=False)

print(df)
#display the minimum value per bin per year
print('\nmin B value per bin:\n',df_low.groupby(['year','B_bin_by_year'])['B'].min().unstack())
