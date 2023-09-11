import spacy
import os
import time
import re
import sys

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# text cleaning and de-identification 
def clean_text(file_path):
    with open(file_path, "r") as file:
        text = file.read()

        # Convert to lowercase
        # text = text.lower()

        # Remove line breaks
        text = text.replace("\n", " ")

        # Remove carriage returns
        text = text.replace("\r", "")

       # Find and mask dates following "dob" or "date of birth"
        dob_pattern = r"(?i)(dob|date of birth)\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})"
        dob_matches = re.findall(dob_pattern, text)
        for match in dob_matches:
            dob_text = match[0] + ":" + match[1]
            redacted_text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '[**REDACTED**]', dob_text)
            text = text.replace(dob_text, redacted_text)

        # Find and mask phone numbers
        phone_pattern = r"\{[^}]*\}\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\s*\(\d{3}\s*\}\s*\d{3}[-.\s]?\d{4}"
        phone_matches = re.findall(phone_pattern, text)
        for match in phone_matches:
            text = text.replace(match, "[**REDACTED**]")

        # Process the text with spaCy for Named Entity Recognition (NER)
        doc = nlp(text)

        # Mask names and addresses recognized by spaCy's NER
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE"]:
                text = text.replace(ent.text, "[**REDACTED**]")

        # Remove special characters like '==' and '−−'
        text = re.sub(r"={2,}", "", text)
        text = re.sub(r"−{2,}", "", text)

        # Remove extra whitespaces
        text = re.sub(r"\s+", " ", text)

        return text

# all directories: OCR result directories, clean data directories, all previous processed files
input_directory = "/ghphi/data/phi/OCRopus_results/OCR_breast_cancer3"
clean_data_directory = "/ghphi/data/phi/clean_reports/breast_cancer_clean_reports3"
processed_file_paths_file = "/ghdevhome/home/cpan/notebooks/processed_file_paths.txt"

# Load processed file paths from a text file (if it exists)
processed_file_paths = set()
if os.path.exists(processed_file_paths_file):
    with open(processed_file_paths_file, "r") as f:
        processed_file_paths = set(f.read().splitlines())

# start time the cleaning and de-identification 
total_cleaning_time = 0
num_processed_files = 0
processed_folders = 0

if len(sys.argv) > 1:
    task_id = int(sys.argv[1])
    batch_size = int(sys.argv[2])
    start_index = (task_id - 1) * batch_size
    end_index = task_id * batch_size
    
    # Iterate over each folder in the input directory
    for folder_name in os.listdir(input_directory):
        folder_path = os.path.join(input_directory, folder_name)
        
        # Check if the path is a directory
        if os.path.isdir(folder_path):
            # Create the corresponding output folder in the clean_data_directory
            output_folder_path = os.path.join(clean_data_directory, folder_name)
            os.makedirs(output_folder_path, exist_ok=True)
            
            # Process each text file within the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                # Process only text files that haven't been processed before
                if file_name.endswith(".txt") and file_path not in processed_file_paths:
                    # Initialize cleaned text
                    cleaned_text = ""
    
                    try:
                        # Record start time
                        start_time = time.time()
    
                        # Clean the text
                        cleaned_text = clean_text(file_path)
    
                        # Record end time
                        end_time = time.time()
    
                        # Calculate cleaning time
                        cleaning_time = end_time - start_time
    
                        # Accumulate total cleaning time and count
                        total_cleaning_time += cleaning_time
                        num_processed_files += 1
    
                        # Add the file path to the processed file paths set
                        processed_file_paths.add(file_path)
    
                        # Create the output file path in the output folder
                        output_file_path = os.path.join(output_folder_path, file_name)
    
                        # Save the cleaned text to the output file
                        with open(output_file_path, "w") as output_file:
                            output_file.write(cleaned_text)
                            print(f"Cleaned file saved: {output_file_path}")
    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
        processed_folders+=1
        # print(f"Cleaned folder saved: {output_folder_path}")
        
    # Save the updated processed file paths to the text file
    with open(processed_file_paths_file, "w") as f:
        f.write("\n".join(processed_file_paths))
    
    # Calculate average cleaning time
    if num_processed_files > 0:
        average_cleaning_time = total_cleaning_time / num_processed_files
    else:
        average_cleaning_time = 0
    
    print(f"Total Cleaning Time: {total_cleaning_time:.2f} seconds")
    print(f"Average Cleaning Time per Document: {average_cleaning_time:.2f} seconds")
    
    # count the percentage of non-empty folders in the cleaning result
    def count_non_empty_files_folders(clean_data_directory):
        # Initialize counters
        total_files = 0
        non_empty_files = 0
        non_empty_folders = 0
        
        # Iterate through all subdirectories in the clean_data_directory
        for root, dirs, files in os.walk(clean_data_directory):
            # Check if there are text files in the current directory
            if any(file_name.endswith(".txt") for file_name in files):
                non_empty_folders += 1
            
            for file_name in files:
                if file_name.endswith(".txt"):
                    total_files += 1
                    file_path = os.path.join(root, file_name)
                    with open(file_path, "r") as file:
                        content = file.read()
                        if content.strip():  # Check if content is non-empty
                            non_empty_files += 1
        
        # Calculate percentages
        percentage_non_empty_files = (non_empty_files / total_files) * 100 if total_files > 0 else 0
        percentage_non_empty_folders = (non_empty_folders / len(os.listdir(clean_data_directory))) * 100
        
        # Print the results
        print(f'non-empty text files counts: {non_empty_files}')
        print(f"Percentage of non-empty text files: {percentage_non_empty_files:.2f}%")
        print(f'non-empty folders counts: {non_empty_folders}')
        print(f"Percentage of non-empty folders: {percentage_non_empty_folders:.2f}%")
    
    count_non_empty_files_folders(clean_data_directory)

else:
    print("Usage: python your_script_name.py <batch_number>")
