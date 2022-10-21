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
    (str, str) -> list
    This function is used to extract data from a specifc baseline acq (acq_id) of subject (sub_id) and concatenate them together. 
    '''
    # set directory & file names
    data_dir = os.path.join(base_dir, 'bids_data','rs_postfmriprep', f'sub-{sub_id}')
    acq1_filename = f'sub-{sub_id}_ses-wave1_task-rest_acq-1_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'
    acq2_filename = f'sub-{sub_id}_ses-wave1_task-rest_acq-2_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'
    # extract data from each acq
    acq1_data = Brain_Data(load_img(os.path.join(data_dir, acq1_filename)))
    acq2_data = Brain_Data(load_img(os.path.join(data_dir, acq2_filename)))
    # concatenate both acq
    data_concate = acq1_data.append(acq2_data)

    return [data_concate, acq1_data, acq2_data]

def load_covariates(base_dir, sub_id):
    '''
    (str, str) -> list
    This function load the covariates tsv files of the given acq(acq_id). 
    '''
    cov_dir = os.path.join(base_dir, 'bids_data', 'rs_derivatives','fmriprep', f'sub-{sub_id}', 'ses-wave1', 'func')
    cov_fileName_1 = f'sub-{sub_id}_ses-wave1_task-rest_acq-1_bold_confounds.tsv'
    cov_fileName_2 = f'sub-{sub_id}_ses-wave1_task-rest_acq-2_bold_confounds.tsv'

    covariates_1 = pd.read_csv(os.path.join(cov_dir, cov_fileName_1), sep = '\t')
    covariates_2 = pd.read_csv(os.path.join(cov_dir, cov_fileName_2), sep = '\t')

    cov_concate = pd.concat([covariates_1, covariates_2]).reset_index()

    return [cov_concate, covariates_1, covariates_2]

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

def make_design_matrix_noWM(data, covariates, tr):
    '''
    (Brain_Data, Data_Frame, float) -> 
    This function will make a design matrix with the seed regressor and nusiance regressor including, motion, CSF, whitematter & spikes
    '''

    other_cov = covariates[['CSF']].apply(zscore)
    mc = make_motion_covariates(covariates, tr)
    spikes = data.find_spikes(global_spike_cutoff=3, diff_spike_cutoff=3)
    dm = Design_Matrix(pd.concat([other_cov, mc, spikes.drop(labels='TR', axis=1)], axis=1), sampling_freq=1/tr)
    dm = dm.add_poly(order=2, include_lower=True)

    return dm

# set subject ID from the imput 
#parser = argparse.ArgumentParser(description='subject level rs connectivity analysis')
#parser.add_argument(
#    '--sub-id',
#    required=True,
#    action='store',
#    help='subject id')
#args = parser.parse_args()

# set dataset parameter
base_dir = '/home/kcheung3/sanlab/DEV_RS/'
bids_base_dir = '/projects/sanlab/shared/DEV/'
sub_list_dir = os.path.join(base_dir, 'baseline_analysis', 'baseline_include_subjectList.txt')
sub_list_file = open(sub_list_dir, "r")
sub_list = sub_list_file.read().split("\n")
sub_list_file.close()
tr = 0.78

# load the parcellation mask
mask_dir = os.path.join(base_dir, 'baseline_analysis')
mask = Brain_Data(os.path.join(mask_dir, 'Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm.nii.gz'))
mask_x = expand_mask(mask)

for sub_id in sub_list: 
    
    print('start with subject', sub_id)
    
    data_list = extractData(bids_base_dir, sub_id)
    covariates_list = load_covariates(bids_base_dir, sub_id)

    # load the concatenated data
    data = data_list[0]
    # load the present covariates
    covariates = covariates_list[0]
    # make a design matrix
    dm = make_design_matrix(data, covariates, tr)
    data.X = dm
    # denoise the data
    stats = data.regress()
    data_denoised = stats['residual']
    # extract time series of each roi
    rois_data = data_denoised.extract_roi(mask=mask)
    # compute pair-wise correlation
    roi_corr = 1 - pairwise_distances(rois_data, metric='correlation')
    # write the correlation to file
    fileName = sub_id + '_concat_corr.csv'
    output_dir = os.path.join(base_dir, 'baseline_analysis', 'subject_correlation', 'baseline_acq_schaefer', fileName)
    corr_df = pd.DataFrame(roi_corr)
    corr_df.to_csv(output_dir, index=False, header=False)
