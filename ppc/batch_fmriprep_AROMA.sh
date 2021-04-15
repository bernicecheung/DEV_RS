#!/bin/bash
#
# This batch file calls on your subject list (which contains both ID and wave number: SID000,wave1). 
# And runs the job_fmriprep.sh file for each subject. 
# It saves the ouput and error files in specified directories.
#
# Set your directories

container=containers/fmriprep-latest-2018-09-05.simg
freesurferlicense=/projects/sanlab/shared/containers/license.txt
group_dir=/projects/sanlab/shared/ #set path to directory within which study folder lives
study=DEV
study_dir="${group_dir}""${study}"
output_dir="${study_dir}"/"${study}"_scripts/fMRI/ppc/output

if [ ! -d "${output_dir}" ]; then
    mkdir -v "${output_dir}"
fi


# Set subject list
subject_list=`cat subject_list_rs.txt` 

pre_subid=""
pre_sessionid=""

# Loop through subjects and run job_mriqc
for subject in $subject_list; do
	subid=`echo $subject | awk -F "," '{print $1}'`
	sessid=`echo $subject | awk -F "," '{print $2}'`
	echo $subid, $sessid
	if [ "$subid" == "$pre_subid" ] && [ "$sessid" == "$pre_sessionid" ]; then
		echo "same session"
		continue
	fi
	prepOutput_dir="${study_dir}"/bids_data/rs_derivatives/fmriprep/sub-"$subid"/ses-"$sessid"/func
	[ -d "${prepOutput_dir}" ] && { prep_files=$(find $prepOutput_dir -name "*acq-1*" | wc -l)
	if [ "$prep_files" == 5 ]; then
		echo "skip"
		continue
	fi; }
	sbatch --export ALL,subid=${subid},sessid=${sessid},group_dir=${group_dir},study_dir=${study_dir},study=${study},container=${container},freesurferlicense=${freesurferlicense} \
		   --job-name fmriprep \
		   --partition=ctn \
		   --cpus-per-task=8 \
		   --mem=10G \
		   -o "${output_dir}"/"${subid}"_"${sessid}"_fmriprep_AROMA_output.txt \
		   -e "${output_dir}"/"${subid}"_"${sessid}"_fmriprep_AROMA_error.txt \
		   --account=sanlab \
		   job_fmriprep_rs.sh
	pre_subid=$subid
	pre_sessionid=$sessid
done