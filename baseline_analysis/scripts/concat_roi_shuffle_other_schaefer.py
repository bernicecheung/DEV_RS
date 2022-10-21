import os
import glob
import re
import argparse
import numpy as np
import pandas as pd
import functools
import pingouin as pg

# set input parameters
parser = argparse.ArgumentParser(description='boostrap correlation')
parser.add_argument(
    '--dv',
    required=True,
    action='store',
    help='dv name')

args = parser.parse_args()

# set study parameter
base_dir = '/home/kcheung3/sanlab/DEV_RS'
output_dir = os.path.join(base_dir, 'baseline_analysis', 'graph_shuffle_outputs')
shuffle_time = 1000
idx_type = 'roi'
dv_name = args.dv

def load_index(index_type):
    '''
    (str) -> dict, list
    This function imports the index for each shuffle for each ROI/edges
    '''
    # set the file directory parameters
    idx_dir = os.path.join(base_dir, 'baseline_analysis', 'shuffle_index', f'{index_type}_shuffle_schaefer')
    idx_fileNames = glob.glob(os.path.join(idx_dir, '*.csv'))

    # initiate a dictionary
    idx_dict = {}
    for file in idx_fileNames:
        inx_df = pd.read_csv(file, sep=',', header=None)
        shuffle_key = re.split('[/_.]', file)[len(re.split('[/_.]', file))-2]
        idx_dict[shuffle_key] = inx_df
    
    return idx_dict

def other_metric_shuffle(dv_df, dv_name, metric_df, idx_df, shuffle_time):
    # initiate parameters
    metric_dv_shuffle_l = []
    # loop through each ROI and calculate correlations
    for (columnName, columnData) in metric_df.iloc[:,1:4].iteritems():
        # initiate a list
        corr_list = []
        # extract the graph metric
        conn_list = columnData.values
        for i in range(shuffle_time): 
            # re-order the dv & cov: 
            dv_shuffle = dv_df[dv_name][idx_df.iloc[i]].values
            age_shuffle = dv_df['age'][idx_df.iloc[i]].values
            gender_shuffle = dv_df['gender'][idx_df.iloc[i]].values
            # generate a dataframe with all shuffled data
            pcorr_df = pd.DataFrame(
                {"conn_list" : conn_list,
                "age_shuffle": age_shuffle,
                "gender_shuffle": gender_shuffle, 
                "dv_shuffle": dv_shuffle}
            )
            # dummy code the gender variable
            pcorr_df_recode = pd.get_dummies(pcorr_df)
            # calculate the partial correlation between roi weights and the dv controlling for age
            pcorr= pg.partial_corr(data= pcorr_df_recode, x='conn_list', y='dv_shuffle', covar=['age_shuffle', 'gender_shuffle_Female'], method='spearman').iloc[0,1]
            # append the partial coefficient to the output list 
            corr_list.append(pcorr)
        corr_df = pd.DataFrame(corr_list, columns = [columnName])
        metric_dv_shuffle_l.append(corr_df)
    
    metric_dv_shuffle_df = pd.concat(metric_dv_shuffle_l, axis = 1)

    return metric_dv_shuffle_df

# load the physio data set
base_dv = pd.read_csv(os.path.join(base_dir, 'dv_data', 'outputs', 'sub_data_baseline_w_clean.csv'))

# extract the included subject list 
include_sid = list(base_dv['SID'])

# extract the physio dv as a lsit
dv_df = base_dv[[dv_name, 'age', 'gender']]

# extract the index
idx_dic = load_index(idx_type)

# use the shuffle index fot ROI 0
idx_df = idx_dic['0']

# load metric dataframe
metric_dir = os.path.join(base_dir, 'baseline_analysis', 'graph_outputs')
metric_df = pd.read_csv(os.path.join(metric_dir, f'other_metric_df_concat.csv'), sep = ',')

# shuffle the partial correlation between each graph metric and the dv
metric_dv_shuffle_df = other_metric_shuffle(dv_df, dv_name, metric_df, idx_df, shuffle_time)

metric_dv_shuffle_df.to_csv(os.path.join(output_dir, f'other_metric_{dv_name}_concat_boost.csv'),index=False, header=True)

