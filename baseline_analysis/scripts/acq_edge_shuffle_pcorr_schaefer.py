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
    '--acq',
    required=True,
    action='store',
    help='acquisition id')
parser.add_argument(
    '--dv',
    required=True,
    action='store',
    help='dv name')
parser.add_argument(
    '--idx_type',
    required=True,
    action='store',
    help='roi or edge')
parser.add_argument(
    '--idx_min',
    required=True,
    action='store',
    help='the lower bound of the index range')
parser.add_argument(
    '--idx_max',
    required=True,
    action='store',
    help='the upper bound of the index range')
args = parser.parse_args()

# set study parameter
base_dir = '/home/kcheung3/sanlab/DEV_RS'
output_dir = os.path.join(base_dir, 'baseline_analysis', 'edge_dv_shuffle_schaefer')
shuffle_time = 1000
idx_min = args.idx_min
idx_max = args.idx_max
acq_id = args.acq
dv_name = args.dv
idx_type = args.idx_type

def load_index(index_type, idx_min, idx_max):
    '''
    (str) -> dict, list
    This function imports the index for each shuffle for each ROI/edges
    '''
    # set the file directory parameters
    idx_dir = os.path.join(base_dir, 'baseline_analysis', 'shuffle_index', f'{index_type}_shuffle_schaefer')
    idx_fileNames = glob.glob(os.path.join(idx_dir, '*.csv'))

    # initiate a dictionary
    idx_dict = {}
    edge_list = []

    for file in idx_fileNames[int(idx_min):int(idx_max)]:
        inx_df = pd.read_csv(file, sep=',', header=None)
        shuffle_key = re.split('[/_.]', file)[len(re.split('[/_.]', file))-2]
        edge_list.append(shuffle_key)
        idx_dict[shuffle_key] = inx_df
    
    return idx_dict, edge_list

def extract_corr_edge(acq_id, include_sid):
    '''
    (str, str) -> DataFrame
    This function imports the correlation matrix of each subject and extract the upper triangle value, then merge all subject data into one dataframe.
    Each row represents an edge between two nodes (labeled with column node_1 & node_2), and each column represents a subject
    '''
    # set file directory parameters
    corr_dir = os.path.join(base_dir, 'baseline_analysis', 'subject_correlation', 'baseline_acq_schaefer')
    corr_fileNames = glob.glob(os.path.join(corr_dir, f'*_{acq_id}_corr.csv'))
    # initiate a list for the dataframes across all subjects
    edge_corr_dfList = []

    for file in corr_fileNames: 
        sub_df = pd.read_csv(file, sep=',', header=None) # load the correlation matrix df of a given subject
        sub_id= re.split('/|_', file)[len(re.split('/|_', file))-3] # extract subject id
        if sub_id not in include_sid: 
            continue
        mask = np.triu(np.ones(sub_df.shape), k = 1).astype(bool).reshape(sub_df.size) # create a mask for the upper triangle
        sub_df_stack = sub_df.stack()[mask].reset_index() # transform the upper triangle into a long-format dataset
        sub_df_stack.columns = ['node_1','node_2',sub_id] # rename the dataframe
        edge_corr_dfList.append(sub_df_stack) # store in the lits

    # merge all individual dataframe
    edge_corr_df = functools.reduce(lambda x, y: pd.merge(x, y, on=["node_1", "node_2"]), edge_corr_dfList)

    return edge_corr_df

def conn_corr_shuffle(dv_df, dv_name, conn_df, idx_dic, edge_list, shuffle_time):
    # initiate parameters
    edge_dv_shuffle_l = []
    # loop through each edge and calculate correlations
    for edge in edge_list:
        # extract shuffle index
        idx_df = idx_dic[edge]
        # initiate a list
        corr_list = []
        # extract the centrality
        conn_list = conn_df.iloc[int(edge), 2:]
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
            # calculate the partial correlation between edge weights and the dv controlling for age
            pcorr= pg.partial_corr(data= pcorr_df_recode, x='conn_list', y='dv_shuffle', covar=['age_shuffle', 'gender_shuffle_Female'], method='spearman').iloc[0,1]
            # append the partial coefficient to the output list 
            corr_list.append(pcorr)
        corr_df = pd.DataFrame(corr_list, columns = [edge])
        edge_dv_shuffle_l.append(corr_df)
    
    edge_dv_shuffle_df = pd.concat(edge_dv_shuffle_l, axis = 1)

    return edge_dv_shuffle_df

# load the physio data set
base_dv = pd.read_csv(os.path.join(base_dir, 'dv_data', 'outputs', 'sub_data_baseline_w_clean.csv'))

# extract the included subject list 
include_sid = list(base_dv['SID'])

# extract the physio dv as a lsit
dv_df = base_dv[[dv_name, 'age', 'gender']]

# extract the index
idx_dic, edge_list = load_index(idx_type, idx_min, idx_max)

conn_df = extract_corr_edge(acq_id, include_sid)

# boostrap the correlation between the brain data and the physio data 
brain_physio_boost = conn_corr_shuffle(dv_df, dv_name, conn_df, idx_dic, edge_list, shuffle_time)

brain_physio_boost.to_csv(os.path.join(output_dir, f'{dv_name}_acq{acq_id}_{idx_type}_boost_{idx_min}_{idx_max}.csv'),index=False, header=True)

