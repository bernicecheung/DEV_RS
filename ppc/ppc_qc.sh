#!/bin/bash

# This script extract the subject ID, wave ID and acq ID from the post ppc with a crash report

# set the post ppc data directory
post_ppc_dir=/projects/sanlab/shared/DEV/bids_data/rs_postfmriprep/

# loop through each crash report
cd $post_ppc_dir
crash_files=$(find -name "crash-*datasource*.txt")
for file in $crash_files; do

    # extract the second line from the crash report
    id_line=$(sed '2q;d' ${file})

    # extract the subID, waveID and acqID
    subid=`echo $id_line | awk -F '/' '{print $11}'`
    waveid=`echo $id_line | awk -F '/' '{print $12}'`
    acqid=`echo $id_line | awk -F '/' '{print $13}'`
    
    echo $subid,$waveid,$acqid

    # write the output into a file
    printf '%s,%s,%s\n' "$subid" "$waveid" "$acqid" >> /projects/sanlab/shared/DEV/DEV_scripts/rsfMRI/ppc/post_ppc_crash.txt
done

