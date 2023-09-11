import os
import re
import time
import json
import sys

def extract_actual_tests(text, test):
    """
    Extracts the actual test names mentioned in the text based on the occurrence of the test name.
    """
    actual_tests = re.findall(r'\b{}\b'.format(re.escape(test)), text)
    return actual_tests

def extract_pages(text):
    """
    Extracts the entire content from the text file.
    """
    return text.strip()

def extract_patient_id(foldername):
    """
    Extracts the patient ID from a given foldername using regular expressions.
    """
    pattern = r'([A-Za-z]\d+)_?.*$'
    match = re.search(pattern, foldername)
    if match:
        return match.group(1)
    else:
        return None

def count_non_empty_files_folders(clean_data_directory):
    # Initialize counters
    total_files = 0
    non_empty_files = 0
    non_empty_folders = 0
    empty_folders = []
    
    # Iterate through all subdirectories in the clean_data_directory
    for root, dirs, files in os.walk(clean_data_directory):
        has_non_empty_text_file = any(file_name.endswith(".txt") and os.path.getsize(os.path.join(root, file_name)) > 0 for file_name in files)
        
        if has_non_empty_text_file:
            non_empty_folders += 1
        else:
            empty_folders.append(os.path.basename(root))  # Add empty folder name
        
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
    
    # Return list of empty folder names
    return empty_folders

    
def extract_test_results_with_pages(directory, empty_folders, company_test_list):
    patient_ids = set()  # To keep track of unique patient IDs
    test_results = []

    total_extraction_time = 0
    total_files_processed = 0
    total_documents_processed = 0

    # Iterate over each folder (representing a document) in the directory
    for foldername in os.listdir(directory):
        if foldername in empty_folders: 
            continue
        patient_id = extract_patient_id(foldername)
        if patient_id is None or patient_id in patient_ids:
            continue 
        patient_ids.add(patient_id)
        folder_path = os.path.join(directory, foldername)

        if os.path.isdir(folder_path) and len(os.listdir(folder_path)) > 0:
            start_time_doc = time.time()

            # Iterate over each file (representing a page) in the folder
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, 'r') as file:
                        text = file.read()

                        start_time_file = time.time()

                        # Extract the tests from the text
                        extracted_tests = set()  
                        actual_tests = []  
                        for test in company_test_list:
                            test_lower = test.lower()
                            if test_lower in ["assure", 'xt', 'xf', 'xf+']:
                                actual_tests.extend(extract_actual_tests(text, test))
                            else:
                                actual_tests.extend(extract_actual_tests(text.lower(), test_lower))

                        end_time_file = time.time()
                        total_extraction_time += end_time_file - start_time_file
                        total_files_processed += 1

                        # Append the test results for this file to the list
                        if actual_tests:
                            test_info = {
                                "file_name": os.path.join(foldername, filename),
                                "patient_id": patient_id,
                                "tests": actual_tests,
                                "page_content": extract_pages(text)
                            }

                            # Extract context window around the extracted tests
                            context_window = 60  # Set your desired context window size
                            context_texts = []
                            for test_name in actual_tests:
                                pattern = re.compile(rf'(.{{0,{context_window}}}{re.escape(test_name)}.{{0,{context_window}}})', re.IGNORECASE)
                                matches = pattern.findall(text)
                                context_texts.extend(matches)

                            test_info["context"] = context_texts
                            test_results.append(test_info)

            end_time_doc = time.time()
            total_documents_processed += 1

    avg_extraction_time_per_file = total_extraction_time / total_files_processed if total_files_processed > 0 else 0
    avg_extraction_time_per_doc = total_extraction_time / total_documents_processed if total_documents_processed > 0 else 0

    print(f"Total time taken: {total_extraction_time:.2f} seconds")
    print(f"Average time per file: {avg_extraction_time_per_file:.2f} seconds")
    print(f"Average time per document: {avg_extraction_time_per_doc:.2f} seconds")

    return test_results

def save_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    if len(sys.argv) != 3:
        print("Usage: python text_results_extraction.py SGE_TASK_ID batch_size")
        sys.exit(1)
    
    sge_task_id = int(sys.argv[1])
    batch_size = int(sys.argv[2])
    
    company_test_list = ['Guardant360 CDx', 'Guardant360', 'Guardant360 TissueNext', 'FoundationOne Liquid', 'xF', 'xF+', 'Assure', 'Plasma Focus', 'Liquid Hallmark', 'Genestrat, InVisionFirst-Lung',
                     'FoundationOne CDx', 'Caris Molecular Intelligence', 'xT', 'OncoExtra', 'Altera', 'Invitae Cancer Screen', 'MyRisk', 'MyChoice']
                     
    text_files_directory = "/ghphi/data/phi/clean_reports/breast_cancer_clean_reports3/"
    
    all_tests = []
    
    for sge_task_id in range(1, 321):
        start_range = (sge_task_id - 1) * batch_size + 1
        end_range = sge_task_id * batch_size

        empty_folders = count_non_empty_files_folders(text_files_directory)
        # Append the extracted test results to the all_tests list
        tests = extract_test_results_with_pages(text_files_directory, empty_folders, company_test_list)
        all_tests.append(tests)
        
    extracted_test_results_file_name = 'labeled_test_results_all.json'
    save_json_file_path = '/ghphi/data/phi/clean_test_results/' + extracted_test_results_file_name
    
    save_json(all_tests, save_json_file_path)

if __name__ == "__main__":
    main()
