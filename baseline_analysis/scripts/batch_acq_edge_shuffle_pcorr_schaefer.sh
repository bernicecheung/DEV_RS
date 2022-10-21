#!/bin/bash
#
# This batch file calls on the subject list (which contains subjectID, waveID and acquisitionID)
# and run the job_ppc_post.sh for each acq. 
# It saves the output and error files in specified directories.

# Set the environment
module load anaconda3
conda activate dev_rs_env

# Set the directories
output_dir=/home/kcheung3/sanlab/DEV_RS/baseline_analysis/outputs/

# Set index list
idx_list=`cat /home/kcheung3/sanlab/DEV_RS/baseline_analysis/idx_list_schaefer.txt`

# Set analysis parameter
acq_id=2
dv=Body_fat_s1

# Loop through subjects
for idx in $idx_list; do
    idx_min=`echo $idx | awk -F ',' '{print $1}'`
	idx_max=`echo $idx | awk -F ',' '{print $2}'`
    
    echo $idx_min, $idx_max
    
    sbatch --export ALL,idx_min=${idx_min},idx_max=${idx_max},acq_id=${acq_id},dv=${dv} \
           --job-name edge_boostrap \
		   --partition=ctn \
		   --cpus-per-task=2 \
		   --mem=2G \
		   --time=23:00:00 \
		   -o "${output_dir}"/"${dv}"_acq"${acq_id}"_"${idx_min}"_"${idx_max}"_schaefer.txt \
		   -e "${output_dir}"/"${dv}"_acq"${acq_id}"_"${idx_min}"_"${idx_max}"_schaefer..txt \
		   --account=sanlab \
		   /home/kcheung3/sanlab/DEV_RS/baseline_analysis/scripts/job_acq_edge_shuffle_pcorr_schaefer.sh
done