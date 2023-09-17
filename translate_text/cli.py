"""
Module that contains the command line app.
"""
import os
import argparse
from google.cloud import storage
from googletrans import Translator



gcp_project = "ac215-project"
bucket_name = "mega-pipeline-bucket"
input_audios = "input_audios"
text_prompts = "text_prompts"
text_paragraphs = "text_paragraphs"
text_translated = "text_translated"

def download():

    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Find all content in a bucket
    blobs = bucket.list_blobs(prefix="text_paragraphs/")

    # input audios
    os.makedirs(text_paragraphs, exist_ok=True)

    for blob in blobs:
        print(blob.name)
        if not blob.name.endswith("/"):
            blob.download_to_filename(blob.name)

def translate():

    translator = Translator()
    os.makedirs(text_translated, exist_ok=True)

    for para in [f"{text_paragraphs}/{doc}" for doc in os.listdir(text_paragraphs)]:
        with open(para, "r") as f:
            input_text = f.read()

        results = translator.translate(input_text, src="en", dest="hi")
        with open(f"{text_translated}/{para.split('/')[1]}", "w") as f:
            f.write(results.text)
                     
def upload():
    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Destination path in GCS 
    blob_files = os.listdir(text_translated)
    destination_blob_names = [f"{text_translated}/{blob_file}" \
                                                     for blob_file in blob_files]
    for destination_blob in destination_blob_names:
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(destination_blob)


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.translate:
        translate()
    if args.upload:
        upload()

if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Translate English to Hindi')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download text paragraphs from GCS bucket")

    parser.add_argument("-t", "--translate", action='store_true',
                        help="Translate text")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload translated text to GCS bucket")

    args = parser.parse_args()

    main(args)