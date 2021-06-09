#!/bin/bash
#
# This batch file calls on the subject list (which contains subjectID, waveID and acquisitionID)
# and run the job_ppc_post.sh for each acq. 
# It saves the output and error files in specified directories.

# Set the environment
module load anaconda3
conda activate dev_rs_env
module load fsl/5.0.10

# Set the directories
output_dir=/projects/sanlab/shared/DEV/DEV_scripts/rsfMRI/baseline_analysis/outputs/

# Set subject list
subject_list=`cat /projects/sanlab/shared/DEV/DEV_scripts/rsfMRI/baseline_analysis/baseline_connectivity_subjectList_0609.txt` 

# Loop through subjects
for subject in $subject_list; do
    subid=`echo $subject | awk -F ',' '{print $1}'`
    
    echo $subid
    
    sbatch --export ALL,subid=${subid} \
           --job-name subject_connect \
		   --partition=ctn \
		   --cpus-per-task=2 \
		   --mem=8G \
		   --time=10:00:00 \
		   -o "${output_dir}"/"${subid}"_subject_connect_output.txt \
		   -e "${output_dir}"/"${subid}"_subject_connect_error.txt \
		   --account=sanlab \
		   /projects/sanlab/shared/DEV/DEV_scripts/rsfMRI/baseline_analysis/scripts/job_subject_level_wholeBrain.sh
done