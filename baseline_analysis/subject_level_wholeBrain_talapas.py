"""
Author: Bernice Cheung 
Date: 06/07/21

This script is for computing subject level degree centrality based on baseline wholebrain connectivity. 
"""

import os
import argparse
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.core import base
import seaborn as sns
import pingouin as pg
from nilearn.image import load_img
from nltools.data import Brain_Data, Design_Matrix, Adjacency
from nltools.mask import expand_mask, roi_to_brain
from nltools.stats import zscore, fdr, one_sample_permutation
from nltools.file_reader import onsets_to_dm
from nltools.plotting import component_viewer
from scipy.stats import binom, ttest_1samp
from sklearn.metrics import pairwise_distances
from copy import deepcopy
import networkx as nx
from nilearn.plotting import plot_stat_map, view_img_on_surf
from bids import BIDSLayout, BIDSValidator
import nibabel as nib


def extractData(base_dir, sub_id):
    '''
    (str, str) -> Brain_Data
    This function is used to extract data from both baseline acq of subject (sub_id) and concatenate them together. 
    '''

    # set directory & file names
    data_dir = os.path.join(base_dir, 'bids_data','rs_postfmriprep', f'sub-{sub_id}')
    acq1_filename = f'sub-{sub_id}_ses-wave1_task-rest_acq-1_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'
    acq2_filename = f'sub-{sub_id}_ses-wave1_task-rest_acq-2_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'
    # extract data from each acq
    acq1_data = Brain_Data(load_img(os.path.join(data_dir, acq1_filename)))
    acq2_data = Brain_Data(load_img(os.path.join(data_dir, acq2_filename)))
    # concatenate both acq
    data = acq1_data.append(acq2_data)

    return data

def load_covariates(base_dir, sub_id):
    '''
    (str) -> DataFrame
    This function load the covariates tsv files of both acq and concatenate them together. 
    '''
    cov_dir = os.path.join(base_dir, 'bids_data', 'rs_derivatives','fmriprep', f'sub-{sub_id}', 'ses-wave1', 'func')
    cov_fileName_1 = f'sub-{sub_id}_ses-wave1_task-rest_acq-1_bold_confounds.tsv'
    cov_fileName_2 = f'sub-{sub_id}_ses-wave1_task-rest_acq-2_bold_confounds.tsv'

    covariates_1 = pd.read_csv(os.path.join(cov_dir, cov_fileName_1), sep = '\t')
    covariates_2 = pd.read_csv(os.path.join(cov_dir, cov_fileName_2), sep = '\t')

    covariates = pd.concat([covariates_1, covariates_2]).reset_index()

    return covariates

def make_motion_covariates(covariates, tr):
    '''
    (DataFrame) -> DataFrame

    This function extract and process motion regressors. This function will be called by make_design_matrix
    '''
    mc = covariates[['X','Y','Z','RotX', 'RotY', 'RotZ']]
    z_mc = zscore(mc)
    all_mc = pd.concat([z_mc, z_mc**2, z_mc.diff(), z_mc.diff()**2], axis=1)
    all_mc.fillna(value=0, inplace=True)
    return Design_Matrix(all_mc, sampling_freq=1/tr)

def make_design_matrix(data, covariates, tr):
    '''
    (Brain_Data, Data_Frame, float) -> 
    This function will make a design matrix with the seed regressor and nusiance regressor including, motion, CSF, whitematter & spikes
    '''

    other_cov = covariates[['CSF', 'WhiteMatter']].apply(zscore)
    mc = make_motion_covariates(covariates, tr)
    spikes = data.find_spikes(global_spike_cutoff=3, diff_spike_cutoff=3)
    dm = Design_Matrix(pd.concat([other_cov, mc, spikes.drop(labels='TR', axis=1)], axis=1), sampling_freq=1/tr)
    dm = dm.add_poly(order=2, include_lower=True)

    return dm

# set subject ID from the imput 
parser = argparse.ArgumentParser(description='subject level rs connectivity analysis')
parser.add_argument(
    '--sub-id',
    required=True,
    action='store',
    help='subject id')
args = parser.parse_args()

# set dataset parameter
base_dir = '/projects/sanlab/shared/DEV/'
sub_id = args.sub_id

# load the concatenated data
data = extractData(base_dir, sub_id)

# load the parcellation mask
mask_dir = os.path.join(base_dir, 'DEV_scripts', 'rsfMRI', 'baseline_analysis')
mask = Brain_Data(os.path.join(mask_dir, 'BN_Atlas_246_2mm.nii.gz'))
mask_x = expand_mask(mask)

# load the concatenated covariates
covariates = load_covariates(base_dir, sub_id)

# make a design matrix
tr = 0.78
dm = make_design_matrix(data, covariates, tr)
data.X = dm

# denoise the data
stats = data.regress()
data_denoised = stats['residual']

# extract time series of each roi
rois_data = data_denoised.extract_roi(mask=mask)

# compute pair-wise partial correlation
rois_df = pd.DataFrame(rois_data.T)
roi_pcorr = rois_df.pcorr().to_numpy()

# soft thresholding the partial correlation
roi_pcorr_thresholded = np.power(((roi_pcorr + 1) / 2 ),6)

# fisher r to z transform
roi_pcorr_thresholded_z = np.arctanh(roi_pcorr_thresholded)

# create a weighted adjacency matrix
a = Adjacency(roi_pcorr_thresholded_z, matrix_type='similarity', labels=[x for x in range(246)])

# generate a network 
G = a.to_graph()
node_and_degree = G.degree()

# create weighted edges
strength = G.degree(weight='weight')
strengths = {node: val for (node, val) in strength}
nx.set_node_attributes(G, dict(strength), 'strength') # Add as nodal attribute

# convert the strength into a data frame
strength_df = pd.DataFrame(list(strengths.values()), columns = [sub_id])
# export the df
fileName = sub_id + '_' + 'strength.csv'
output_dir = os.path.join(base_dir, 'DEV_scripts', 'rsfMRI', 'baseline_analysis', 'subject_connectivity', fileName)
strength_df.to_csv(output_dir, index=False)

# Normalized node strength values 1/N-1
normstrenghts = {node: val * 1/(len(G.nodes)-1) for (node, val) in strength}
nx.set_node_attributes(G, normstrenghts, 'strengthnorm') # Add as nodal attribute

# convert the normalized strength into a data frame
normstrength_df = pd.DataFrame(list(normstrenghts.values()), columns = [sub_id])
# export the df
fileName = sub_id + '_' + 'normstrength.csv'
output_dir = os.path.join(base_dir, 'DEV_scripts', 'rsfMRI', 'baseline_analysis', 'subject_connectivity', fileName)
normstrength_df.to_csv(output_dir, index=False)