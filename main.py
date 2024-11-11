import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from shutil import move

import openai
import assemblyai as aai
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Paths
incoming_bucket = os.getenv("INCOMING_BUCKET", "./incoming_audio")
intermediate_transcripts = os.getenv("INTERMEDIATE_TRANSCRIPTS", "./intermediate_transcripts")
output_folder = os.getenv("OUTPUT_FOLDER", "./output")

# Ensure necessary directories exist
os.makedirs(intermediate_transcripts, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Define paths for the consolidated transcript file and final outputs
consolidated_transcript_file = os.path.join(intermediate_transcripts, "total_transcript.md")
datetime_prefix = datetime.now().strftime("%Y-%m-%d-%H-%M")
transcript_file = os.path.join(output_folder, f"{datetime_prefix}-transcripts.md")
summary_action_file = os.path.join(output_folder, f"{datetime_prefix}-summary_action.md")

# AssemblyAI transcriber instance
transcriber = aai.Transcriber()

def convert_m4a_to_wav(file_path):
    """Converts .m4a files to .wav format."""
    audio = AudioSegment.from_file(file_path, format="m4a")
    wav_path = file_path.replace(".m4a", ".wav")
    audio.export(wav_path, format="wav")
    return wav_path

def transcribe_audio(file_path):
    """Transcribes audio using AssemblyAI, saves intermediate result."""
    transcript_path = os.path.join(intermediate_transcripts, os.path.basename(file_path) + ".txt")
    
    # If already transcribed, load from file
    if os.path.exists(transcript_path):
        with open(transcript_path, 'r') as f:
            return f.read()
    
    print(f"Uploading {file_path} to AssemblyAI for transcription...")
    transcription = transcriber.transcribe(file_path)
    with open(transcript_path, 'w') as f:
        f.write(transcription.text)
    
    return transcription.text

def generate_summary_and_action(transcriptions):
    """Generates summary and action points from the transcriptions."""
    prompt = f"""
    Here is a set of transcriptions from various voice notes. Please provide a summary of the key points, and list actionable items.
    
    Transcriptions:
    {transcriptions}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes and extracts action points."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2500,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()

def process_file(file_path):
    """Process each audio file: Convert, Transcribe, and Save."""
    # Check if an intermediary transcription already exists
    transcript_path = os.path.join(intermediate_transcripts, os.path.basename(file_path) + ".txt")
    if os.path.exists(transcript_path):
        print(f"Intermediary transcription for {file_path} exists. Loading from file.")
        with open(transcript_path, 'r') as f:
            return f.read()
    
    # Convert and transcribe if no intermediary exists
    print(f"Processing {file_path}")
    wav_path = convert_m4a_to_wav(file_path)
    transcription = transcribe_audio(wav_path)
    os.remove(wav_path)
    return transcription

def main():
    # Check if the consolidated transcript file already exists
    if os.path.exists(consolidated_transcript_file):
        print(f"{consolidated_transcript_file} already exists. Skipping transcription.")
        # Load the combined transcription from the existing file
        with open(consolidated_transcript_file, 'r') as tf:
            combined_transcription = tf.read()
    else:
        # Asynchronous transcription with ThreadPoolExecutor
        transcription_texts = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for filename in os.listdir(incoming_bucket):
                if filename.endswith(".m4a"):
                    file_path = os.path.join(incoming_bucket, filename)
                    futures.append(executor.submit(process_file, file_path))
            
            # Collect results as they complete
            for future in futures:
                transcription = future.result()
                if transcription:
                    transcription_texts.append(transcription)
        
        # Combine all transcriptions into a single text
        combined_transcription = "\n\n".join(transcription_texts)
        
        # Write the consolidated transcription to the intermediate consolidated transcript file
        with open(consolidated_transcript_file, 'w') as tf:
            tf.write(combined_transcription)

    # Generate summary and action points
    summary_and_action = generate_summary_and_action(combined_transcription)
    
    # Write the final summary and action points to a markdown file in the output folder
    with open(summary_action_file, 'w') as saf:
        saf.write(summary_and_action)
    
    # Copy consolidated transcript to final transcript file with datetime prefix
    move(consolidated_transcript_file, transcript_file)

    # Clear the incoming bucket
    for filename in os.listdir(incoming_bucket):
        file_path = os.path.join(incoming_bucket, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Clear the intermediate transcription folder
    for filename in os.listdir(intermediate_transcripts):
        file_path = os.path.join(intermediate_transcripts, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    print("Processing complete. Files generated:")
    print(f" - Full transcription: {transcript_file}")
    print(f" - Summary and actions: {summary_action_file}")
    print("Incoming directory and intermediate transcription folder have been cleared.")

# Run the script
if __name__ == "__main__":
    main()
