#!/bin/bash
#$ -N ocr_job
#$ -j y
#$ -o /home/cpan/notebooks/log_files/ocr_job.$SGE_TASK_ID.log
#$ -t 1-320
#$ -l hostname=spec01|spec02|spec03|spec04
#$ -S /bin/bash

# Print the node name where the job is running
echo "Running on node: $HOSTNAME"

# Print the total number of allocated slots (cores)
echo "Total allocated slots: $NSLOTS"

# Print the current task ID
echo "Task ID: $SGE_TASK_ID"

# Load required modules (if needed)
# module load python

# Activate your virtual environment (if using one)
# source /path/to/your/virtualenv/bin/activate
source /home/cpan/.bashrc
conda activate myenv

# Set the value of 'n'
n=640  # number of documents to process 

# Path to the file containing breast cancer PDF paths
file_paths_file="/home/cpan/notebooks/all_billing_pdfs.txt"

# Run your Python script with file paths as argument
python /home/cpan/notebooks/OCRopus_script.py $n $SGE_TASK_ID "$file_paths_file"
