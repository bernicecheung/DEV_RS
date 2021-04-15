#!/bin/bash

# This script runs fmriprep on subjects located in the BIDS directory 
# and saves ppc-ed output and motion confounds
# in the derivatives folder.

# Set bids directories
bids_dir="${group_dir}""${study}"/bids_data
derivatives="${bids_dir}"/rs_derivatives
working_dir="${derivatives}"/working/
image="${group_dir}""${container}"

echo -e "\nfMRIprep on ${subid}_${sessid}"
echo -e "\nContainer: $image"
echo -e "\nSubject directory: $bids_dir"

# Source task list
tasks=`cat tasks.txt`

# Load packages
module load singularity

# Create working directory
mkdir -p $working_dir

# Run container using singularity
cd $bids_dir

#create a temp dir just for this job
job_tempdir=${USER}_${study}_${subid}_${sessid}

mkdir -p /tmp/${job_tempdir}

for task in ${tasks[@]}; do
	echo -e "\nStarting on: $task"
	echo -e "\n"

	PYTHONPATH="" singularity run --bind "${group_dir}":"${group_dir}" $image $bids_dir $derivatives participant \
		--participant_label $subid \
		-t $task \
		-w /tmp \
		--output-space {T1w,template,fsaverage5,fsnative} \
		--nthreads 1 \
		--mem-mb 10000 \
		--fs-license-file $freesurferlicense \
        --use-aroma
		--ignore slicetiming \
		--longitudinal


	echo -e "\n"
	echo -e "\ndone"
	echo -e "\n-----------------------"
done

# clean tmp folder
/usr/bin/rm -rvf /tmp/${job_tempdir}/fmriprep*