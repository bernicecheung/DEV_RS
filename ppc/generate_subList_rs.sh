#!/bin/bash

# This script look through DEV BIDS data and record the subjectIDs
# and session IDs that include resting data data

# set the BIDS data directory
group_dir=/projects/sanlab/shared/ #set path to directory within which study folder lives
study=DEV
bids_dir="${group_dir}""${study}"/bids_data
subList_dir="${group_dir}""${study}"/DEV_scripts/rsfMRI/ppc/

# goes into each subject folder to check if there's resting state data
for dir in */; do
    if [[ "$dir" == *"sub-DEV"* ]] && [[ "$dir" != *"backup"* ]]; then
        cd $dir
        rs_files=$(find -name "*rest*.nii.gz")
        for file in $rs_files; do
            echo $file | awk -F'[-_]' '{print $3, $5, $9}' >>"$subList_dir"subject_list_rs.txt # append the subjectID, sessionID and acqID into the file
        done
        cd ../
    fi
done



#find \( -not -name "*backup*" \) -and \( -name "sub-DEV*" -and -name "*rest*.nii.gz" \)