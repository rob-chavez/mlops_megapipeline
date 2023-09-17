"""
Module that contains the command line app.
"""
import os
import io
import argparse
import ffmpeg
from tempfile import TemporaryDirectory
from google.cloud import storage
from google.cloud import speech



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
    blobs = bucket.list_blobs(prefix="input_audios/")

    # input audios
    os.makedirs(input_audios, exist_ok=True)

    for blob in blobs:
        print(blob.name)
        if not blob.name.endswith("/"):
            blob.download_to_filename(blob.name)

def transcribe():
    # Instantiates a client
    client = speech.SpeechClient()

    audio_path = "input_audios"
    audio_files = os.listdir(audio_path)
    audio_paths = [f"{audio_path}/{audio}" for audio in audio_files]

    for mp3 in audio_paths:

        with TemporaryDirectory() as audio_dir:
            flac_path = os.path.join(audio_dir, "audio.flac")
            stream = ffmpeg.input(mp3)
            stream = ffmpeg.output(stream, flac_path)
            ffmpeg.run(stream)

            with io.open(flac_path, "rb") as audio_file:
                content = audio_file.read()

            # Transcribe
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                language_code="en-US"
            )
            operation = client.long_running_recognize(
                config=config, audio=audio)
            response = operation.result(timeout=90)
            
            if response.results:
                for result in response.results:
                    transcript = result.alternatives[0].transcript
                    print("Transcript: {}".format(transcript))
                    output_path = "text_prompts/"
                    output_text = f"{mp3.split('/')[1][:-1*(len('.mp3'))]}.txt"
                    os.makedirs(output_path, exist_ok=True)
                    with open(f"{output_path}/{output_text}", "w") as f:
                        f.write(transcript)
            else:
                transcript = "No audio found in mp3"
                print("Transcript: {}".format(transcript))
                output_path = "text_prompts/"
                output_text = f"{mp3.split('/')[1][:-1*(len('.mp3'))]}.txt"
                os.makedirs(output_path, exist_ok=True)
                with open(f"{output_path}/{output_text}", "w") as f:
                    f.write(transcript)
                     
def upload():
    # Initiate Storage client
    storage_client = storage.Client(project=gcp_project)

    # Get reference to bucket
    bucket = storage_client.bucket(bucket_name)

    # Destination path in GCS 
    blob_files = os.listdir(text_prompts)
    destination_blob_names = [f"{text_prompts}/{blob_file}" \
                                                     for blob_file in blob_files]
    for destination_blob in destination_blob_names:
        blob = bucket.blob(destination_blob)
        blob.upload_from_filename(destination_blob)


def main(args=None):

    print("Args:", args)

    if args.download:
        download()
    if args.transcribe:
        transcribe()
    if args.upload:
        upload()

if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal 'python cli.py --help', it will provide the description
    parser = argparse.ArgumentParser(
        description='Transcribe audio file to text')

    parser.add_argument("-d", "--download", action='store_true',
                        help="Download audio files from GCS bucket")

    parser.add_argument("-t", "--transcribe", action='store_true',
                        help="Transcribe audio files to text")

    parser.add_argument("-u", "--upload", action='store_true',
                        help="Upload transcribed text to GCS bucket")

    args = parser.parse_args()

    main(args)