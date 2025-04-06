import pandas as pd
import os
import json
import PyPDF2



#Code to save cv to json(Run once!)

def read_pdfs_and_save(folder_path, output_json='pdf_texts.json'):

    all_text_data = {}

    # Iterate over all files in the given folder
    for file_name in os.listdir(folder_path):
        # Process only PDF files
        if file_name.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, file_name)
            
            # Initialize a string to store text for this PDF
            pdf_text = []

            # Open the PDF file in read-binary mode
            with open(pdf_path, 'rb') as file:
                # Create a PdfReader
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from each page
                for page_index in range(len(pdf_reader.pages)):
                    page_text = pdf_reader.pages[page_index].extract_text()
                    if page_text:
                        pdf_text.append(page_text)

            # Combine all page texts into one string
            all_text_data[file_name] = "\n".join(pdf_text)

    # Save the text data dictionary to a JSON file
    with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(all_text_data, json_file, ensure_ascii=False, indent=4)

    print(f"Extracted PDF texts have been saved to {output_json}")
    return all_text_data

cvs = "C:\Louwyn\Python\WASHU User Search\CVs"
CV = read_pdfs_and_save(cvs)






