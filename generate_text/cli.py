"""
Module that contains the command line app.
"""
import os
import argparse
from google.cloud import storage
from transformers import pipeline

gcp_project = "ac215-project"
bucket_name = "mega-pipeline-bucket"
input_audios = "input_audios"
text_prompts = "text_prompts"

def download():

    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Find all content in a bucket
    blobs = bucket.list_blobs(prefix="text_prompts/")

    # input audios
    os.makedirs(text_prompts, exist_ok=True)

    for blob in blobs:
        print(blob.name)
        if not blob.name.endswith("/"):
            blob.download_to_filename(blob.name)

def generate():

    # Create the output directory if it doesn't exist
    os.makedirs("text_paragraphs", exist_ok=True)

    # Initialize the text generation pipeline
    text_generator = pipeline("text-generation")
    
    for i, text_file in enumerate([f"{text_prompts}/{text}" for text in os.listdir(text_prompts)]):

        #get prompt
        with open(text_file, "r") as f:
            prompt = f.readline()

        # Generate text based on the prompt
        generated_text = text_generator(prompt, max_length=100, num_return_sequences=1)[0]["generated_text"]

        # Save the generated text to a file
        filename = os.path.join("text_paragraphs", f"{text_file.split('/')[1]}")
        with open(filename, "w") as file:
            file.write(generated_text.strip("\n"))
                     
def upload():
    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Destination path in GCS 
    destination_blob_names = [f"{'text_paragraphs'}/{blob_file}" \
                              for blob_file in os.listdir("text_paragraphs")]
    for destination_blob in destination_blob_names:
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(destination_blob)


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.generate:
        generate()
    if args.upload:
        upload()

if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Transcribe audio file to text')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download text prompts from GCS bucket")

    parser.add_argument("-g", "--generate", action='store_true',
                        help="Generate a text paragraph")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload paragraph text to GCS bucket")

    args = parser.parse_args()

    main(args)