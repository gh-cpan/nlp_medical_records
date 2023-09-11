#!/usr/bin/env python
# coding: utf-8
import os
import time
import re
import subprocess
from pathlib import Path
import concurrent.futures
from PIL import Image
import pytesseract
import PyPDF2
import pandas as pd
import pickle
import sys

def find_matching_files(destination_dir, patient_ids):
    matching_files = []
    patient_id_set = set(patient_ids)
    patient_id_pattern = re.compile(rf"({'|'.join(patient_ids)})_\d*\.pdf$", re.IGNORECASE)

    if destination_dir.is_dir():
        for file in destination_dir.glob('*.pdf'):
            if file.name.startswith(tuple(patient_id_set)):
                matching_files.append(file)
            elif patient_id_pattern.match(file.name):
                matching_files.append(file)
    return matching_files


def ocr_pdf(file_path):
    # Record start time
    start_time = time.time()

    # Convert PDF to images using OCRopus
    image_output_dir = os.path.join(output_directory, os.path.splitext(os.path.basename(file_path))[0])
    os.makedirs(image_output_dir, exist_ok=True)

    # Use pdfimages to extract images from the PDF
    pdf_images_cmd = ["pdfimages", "-j", file_path, os.path.join(image_output_dir, "image")]
    subprocess.run(pdf_images_cmd)

    # Convert extracted images to PNG format
    for image_file_name in os.listdir(image_output_dir):
        image_file_path = os.path.join(image_output_dir, image_file_name)
        image = Image.open(image_file_path)
        png_file_path = os.path.join(image_output_dir, os.path.splitext(image_file_name)[0] + ".png")
        image.save(png_file_path)

        # Remove the original image file
        os.remove(image_file_path)

    # Process each image file (now in PNG format)
    for image_file_name in os.listdir(image_output_dir):
        image_file_path = os.path.join(image_output_dir, image_file_name)

        # Perform OCR on the image
        image = Image.open(image_file_path)
        text = pytesseract.image_to_string(image)

        # Save the extracted text to a text file
        text_output_dir = os.path.join(output_directory, os.path.splitext(os.path.basename(file_path))[0])
        os.makedirs(text_output_dir, exist_ok=True)
        text_file_name = os.path.splitext(image_file_name)[0] + ".txt"
        text_file_path = os.path.join(text_output_dir, text_file_name)
        with open(text_file_path, "w", encoding="utf-8") as text_file:
            # print("extract text:", text)
            text_file.write(text)

    # Record end time
    end_time = time.time()

    # Calculate time spent
    time_spent = end_time - start_time
    print(f"Time spent on OCR for {os.path.basename(file_path)}: {time_spent:.2f} seconds")



if __name__ == "__main__":
    
    n = int(sys.argv[1])
    task_id = int(sys.argv[2])  
    file_paths_file = sys.argv[3]  # Path to the file containing PDF paths
    
    # Read the list of file paths from the file
    with open(file_paths_file, "r") as f:
        file_paths = f.read().splitlines()
    
    # Calculate start and end indices for the files to process based on task ID and 'n'
    start_index = (task_id - 1) * n
    end_index = start_index + n
    to_process_files = file_paths[start_index:end_index]
    
    # Create the output directory if it doesn't exist
    output_directory = "/ghphi/data/phi/OCRopus_results/OCR_breast_cancer3/"
    os.makedirs(output_directory, exist_ok=True)

    # Check for already processed documents
    processed_documents = set()
    for document_folder in os.listdir(output_directory):
        processed_documents.add(os.path.splitext(document_folder)[0])
    
    # Filter out processed documents from the remaining to_process_files list
    remaining_to_process_files = [file for file in to_process_files if os.path.splitext(os.path.basename(file))[0] not in processed_documents]
    
    # Rest of the documents that are not processed 
    if remaining_to_process_files:
        try:
            # Perform OCR on each remaining PDF file
            start_time = time.time()
    
            # Create a ThreadPoolExecutor with the maximum number of workers (use as many as CPU cores)
            num_workers = os.cpu_count()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # Schedule the ocr_pdf function for each remaining file in the executor
                futures = [executor.submit(ocr_pdf, file) for file in remaining_to_process_files]
    
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
    
            end_time = time.time()
            total_time = end_time - start_time
    
            # Calculate the average OCR time per remaining file
            num_files_processed = len(remaining_to_process_files)
            average_time_per_file = total_time / num_files_processed
    
            print("\nProcessing of remaining documents completed.")
            print(f"Total OCR Time for remaining documents: {total_time:.2f} seconds")
            print(f"Average OCR Time per Remaining File: {average_time_per_file:.2f} seconds")
        except Exception as e:
            print(f"An error occurred during OCR: {e}")
    else:
        print("All documents have already been processed.")




