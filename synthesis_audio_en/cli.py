"""
Module that contains the command line app.
"""
import os
import io
import argparse
from tempfile import TemporaryDirectory
from google.cloud import storage
from google.cloud import texttospeech


gcp_project = "ac215-project"
bucket_name = "mega-pipeline-bucket"
input_audios = "input_audios"
text_prompts = "text_prompts"
text_audios = "text_audios"

def download():

    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Find all content in a bucket
    blobs = bucket.list_blobs(prefix="text_paragraphs/")

    # input audios
    os.makedirs("text_paragraphs", exist_ok=True)

    for blob in blobs:
        print(blob.name)
        if not blob.name.endswith("/"):
            blob.download_to_filename(blob.name)

def synthesis():

    # Instantiates a client

    client = texttospeech.TextToSpeechClient()

    for paras in [f"text_paragraphs/{doc}" for doc in os.listdir("text_paragraphs")]:
        
        with open(paras, "r") as f:
            input_text = f.read()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=input_text)

        # Build the voice request
        language_code = "en-US"
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save the audio file
        os.makedirs(text_audios, exist_ok=True)
        audio_file = f"{text_audios}/{paras.split('/')[1][:-1*len('.txt')]}.mp3"
        with open(audio_file, "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)
                        
def upload():
    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Destination path in GCS 
    blob_files = os.listdir(text_audios)
    destination_blob_names = [f"{text_audios}/{blob_file}" \
                                                    for blob_file in blob_files]
    for destination_blob in destination_blob_names:
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(destination_blob)


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.synthesis:
        synthesis()
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Synthesis audio from text')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download paragraph of text from GCS bucket")

    parser.add_argument("-s", "--synthesis", action='store_true',
                        help="Synthesis audio")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload audio file to GCS bucket")

    args = parser.parse_args()

    main(args)