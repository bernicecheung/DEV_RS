import os
import numpy as np
import pandas as pd
import networkx as nx
from nltools.data import Brain_Data, Design_Matrix, Adjacency
from nltools.mask import expand_mask, roi_to_brain

def coeff_threshold (edge_df, min_percentile, max_percentile, sub_id):
    ''' 
    (DataFrame, int, int)
    This function generate the corresponding edge correlation coefiicents to a range of (min_percentile, max_percentile) with an increment of 1. 
    '''

    # extract the upper triangle of the edge weights, and sort it 
    mask = np.triu(np.ones(edge_df.shape), k = 1).astype(bool).reshape(edge_df.size) # create a mask for the upper triangle
    edge_df_stack = edge_df.stack()[mask].reset_index()
    edge_stack = edge_df_stack.iloc[:,2]
    edge_stack = np.array(sorted(edge_stack, reverse=True))

    # calculate the coefficients corresponding to each percentile
    coeff_threshold = [np.percentile(edge_stack, percentile) for percentile in range(min_percentile,max_percentile,1)]

    # create a dataframe
    coeff_threshold_df = pd.DataFrame(
        {
            "edge_coefficient": coeff_threshold,
            "percentile" : list(range(min_percentile,max_percentile,1)),
            "sub_id" : sub_id
        }
    )

    return coeff_threshold_df

def binary_network (edge_df, coeff_threshold, number_roi): 
    ''' 
    (DataFrame, DataFrame) -> Graph
    This function generate a binary graph object from the edge dataframe based on the threshold (coeff_threshold). 
    '''

    # create a binary network with a spacity of 30%
    a = Adjacency(edge_df, matrix_type='similarity', labels=[x for x in range(number_roi)])
    a_thresholded = a.threshold(upper=coeff_threshold, binarize=True)
    G = a_thresholded.to_graph()

    return G
    

# set study parameter
base_dir = '/home/kcheung3/sanlab/DEV_RS'

# load the physio and self report data set
base_dv = pd.read_csv(os.path.join(base_dir, 'dv_data', 'outputs', 'sub_data_baseline_w_clean.csv'))

# extract the subject ID
sub_ids = list(base_dv['SID'])

# initiate dataframes for metric outcomes
coeff_threshold_list = []
degree_centrality_list = []
betweenness_centrality_list = []
closeness_centrality_list = []
cluster_coefficients_list = []
other_metric_list = []


for sub in sub_ids:
    # load edge weights
    edge_dir = os.path.join(base_dir, 'baseline_analysis', 'subject_correlation', 'baseline_acq_schaefer')
    edge_file = os.path.join(edge_dir, f'{sub}_concat_corr.csv')
    edge_df = pd.read_csv(edge_file, sep=',', header=None)

    # generate coefficient threshold dataframe
    coeff_threshold_df = coeff_threshold (edge_df, 70, 91, sub)
    coeff_threshold_list.append(coeff_threshold_df)

    # generate a binary network based on a spacity level of 30%
    G = binary_network(edge_df, coeff_threshold_df['edge_coefficient'][0], 100)

    # generate network metric
    degree_centrality = list(nx.degree_centrality(G).values())
    betweenness_centrality = list(nx.betweenness_centrality(G).values())
    closeness_centrality = list(nx.closeness_centrality(G).values())
    global_efficiency = nx.global_efficiency(G)
    local_efficiency = nx.local_efficiency(G)
    cluster_coefficients = list(nx.clustering(G, nodes=None, weight=None).values())
    average_coefficients = nx.average_clustering(G, nodes=None, weight=None)

    # convert the lists to dataframes
    degree_centrality_df = pd.DataFrame(degree_centrality, columns = [sub])
    betweenness_centrality_df = pd.DataFrame(betweenness_centrality, columns = [sub])
    closeness_centrality_df = pd.DataFrame(closeness_centrality, columns = [sub])
    cluster_coefficients_df = pd.DataFrame(cluster_coefficients, columns = [sub])
    other_metric_df = pd.DataFrame(
        {
            'sub_id' : sub,
            'global_efficiency' : global_efficiency, 
            'local_efficiency' : local_efficiency,
            'average_coefficients' : average_coefficients,
        },
        index = [sub]
    
    )

    # append to list
    degree_centrality_list.append(degree_centrality_df)
    betweenness_centrality_list.append(betweenness_centrality_df)
    closeness_centrality_list.append(closeness_centrality_df)
    cluster_coefficients_list.append(cluster_coefficients_df)
    other_metric_list.append(other_metric_df)

# concatenate outputs
degree_centrality_df = pd.concat(degree_centrality_list, axis=1)
betweenness_centrality_df = pd.concat(betweenness_centrality_list, axis=1)
closeness_centrality_df = pd.concat(closeness_centrality_list, axis=1)
cluster_coefficients_df = pd.concat(cluster_coefficients_list, axis=1)

coeff_threshold_df = pd.concat(coeff_threshold_list, ignore_index = True)
other_metric_df = pd.concat(other_metric_list)

# write the outputs
output_dir = os.path.join(base_dir, 'baseline_analysis', 'graph_outputs')

degree_centrality_df.to_csv(os.path.join(output_dir, "degree_centrality_df_concat.csv"), index=False, header=True)
betweenness_centrality_df.to_csv(os.path.join(output_dir, "betweenness_centrality_df_concat.csv"), index=False, header=True)
closeness_centrality_df.to_csv(os.path.join(output_dir, "closeness_centrality_df_concat.csv"), index=False, header=True)
cluster_coefficients_df.to_csv(os.path.join(output_dir, "cluster_coefficients_df_concat.csv"), index=False, header=True)
coeff_threshold_df.to_csv(os.path.join(output_dir, "coeff_threshold_df_concat.csv"), index=False, header=True)
other_metric_df.to_csv(os.path.join(output_dir, "other_metric_df_concat.csv"), index=False, header=True)
