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
output_dir=/projects/sanlab/shared/DEV/DEV_scripts/rsfMRI/ppc/output/

# Set subject list
subject_list=`cat subject_list_0607.txt` 

# Loop through subjects
for subject in $subject_list; do
    subid=`echo $subject | awk -F ',' '{print $1}'`
    waveid=`echo $subject | awk -F ',' '{print $2}'`
    acqid=`echo $subject | awk -F ',' '{print $3}'`
    
    echo $subid, $waveid, $acqid
    
    sbatch --export ALL,subid=${subid},waveid=${waveid},acqid=${acqid} \
           --job-name post_ppc \
		   --partition=ctn \
		   --cpus-per-task=2 \
		   --mem=4G \
		   --time=10:00:00 \
		   -o "${output_dir}"/"${subid}"_"${waveid}"_"${acqid}"_post_ppc_output.txt \
		   -e "${output_dir}"/"${subid}"_"${waveid}"_"${acqid}"_post_ppc_error.txt \
		   --account=sanlab \
		   job_post_ppc.sh
done