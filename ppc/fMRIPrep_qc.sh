#!/bin/bash

# This script check the fMRIPrep output and record the runs with errors.

# set the BIDS data directory
group_dir=/projects/sanlab/shared/ #set path to directory within which study folder lives
study=DEV
fMRIPrep_dir="${group_dir}""${study}"/bids_data/rs_derivatives/fmriprep


# move to the fMRIPrep output directory
cd $fMRIPrep_dir

# list the file name with errors into  fMRIPrep_qc.txt 
grep -niL "No errors to report" *.html > fMRIPrep_qc.txt 