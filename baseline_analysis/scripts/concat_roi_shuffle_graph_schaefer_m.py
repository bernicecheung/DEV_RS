import os
import glob
import re
import argparse
import pandas as pd
import pingouin as pg

# set input parameters
parser = argparse.ArgumentParser(description='boostrap correlation')
parser.add_argument(
    '--dv',
    required=True,
    action='store',
    help='dv name')
parser.add_argument(
    '--metric_name',
    required=True,
    action='store',
    help='graph metric name')
args = parser.parse_args()

# set study parameter
base_dir = '/home/kcheung3/sanlab/DEV_RS'
output_dir = os.path.join(base_dir, 'baseline_analysis', 'graph_shuffle_outputs')
shuffle_time = 1000
idx_type = 'roi'
dv_name = args.dv
metric_name = args.metric_name

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

def conn_corr_shuffle(dv_df, dv_name, conn_df, idx_dic, shuffle_time):
    # initiate parameters
    roi_list = [str(x) for x in range(0, 100)]
    roi_dv_shuffle_l = []
    # loop through each ROI and calculate correlations
    for roi in roi_list:
        # extract shuffle index
        idx_df = idx_dic[roi]
        # initiate a list
        corr_list = []
        # extract the centrality
        conn_list = conn_df.iloc[int(roi)]
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
            pcorr= pg.partial_corr(data= pcorr_df_recode, x='conn_list', y='dv_shuffle', covar=['age_shuffle', 'gender_shuffle_Male'], method='spearman').iloc[0,1]
            # append the partial coefficient to the output list 
            corr_list.append(pcorr)
        corr_df = pd.DataFrame(corr_list, columns = [roi])
        roi_dv_shuffle_l.append(corr_df)
    
    roi_dv_shuffle_df = pd.concat(roi_dv_shuffle_l, axis = 1)

    return roi_dv_shuffle_df

# load the physio data set
base_dv = pd.read_csv(os.path.join(base_dir, 'dv_data', 'outputs', 'sub_data_baseline_w_clean.csv'))

# extract the included subject list 
include_sid = list(base_dv['SID'])

# extract the physio dv as a lsit
dv_df = base_dv[[dv_name, 'age', 'gender']]

# extract the index
idx_dic = load_index(idx_type)

# extract graph metric dataframe
metric_dir = os.path.join(base_dir, 'baseline_analysis', 'graph_outputs')
metric_df = pd.read_csv(os.path.join(metric_dir, f'{metric_name}_df_concat.csv'), sep = ',')

# boostrap the correlation between the brain data and the physio data 
brain_physio_boost = conn_corr_shuffle(dv_df, dv_name, metric_df, idx_dic, shuffle_time)

brain_physio_boost.to_csv(os.path.join(output_dir, f'{metric_name}_{dv_name}_concat_boost.csv'),index=False, header=True)

print('analysis completed. The result is saved to', os.path.join(output_dir, f'{metric_name}_{dv_name}_concat_boost_m.csv'))
