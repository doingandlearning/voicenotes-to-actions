# Transcription and Summarization Pipeline

This project provides a pipeline to transcribe audio files (`.m4a` format) using AssemblyAI, summarize the transcriptions, and extract action points with OpenAI's GPT-4 model. It includes support for asynchronous transcription, intermediary storage, and reusable consolidated transcripts for consistent results.

## Features

- Converts `.m4a` files to `.wav` for transcription.
- Asynchronous transcription with intermediary file storage.
- Summarizes transcriptions and extracts action points with GPT-4.
- Stores consolidated transcriptions to avoid redundant work.
- Date-time prefixed output files for organized storage.

## Setup

### 1. Clone the Repository

```bash
git clone git@github.com:doingandlearning/voicenotes-to-actions.git
cd voicenotes-to-actions
```

### 2. Install Dependencies

```bash
pip install openai assemblyai pydub python-dotenv
```

Additionally, ensure `ffmpeg` is installed, as `pydub` requires it to handle `.m4a` files:

#### macOS

```bash
brew install ffmpeg
```

#### Ubuntu/Debian Linux

```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows

Download the `ffmpeg` binary from [FFmpeg's official website](https://ffmpeg.org/download.html) and add it to your system PATH.

### 3. Environment Variables

Create a `.env` file in the root directory of the project. Add the following environment variables:

```plaintext
OPENAI_API_KEY=your_openai_api_key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key

# Directory paths (default values shown)
INCOMING_BUCKET=./incoming_audio
INTERMEDIATE_TRANSCRIPTS=./intermediate_transcripts
OUTPUT_FOLDER=./output
```

- Replace `your_openai_api_key` and `your_assemblyai_api_key` with your actual API keys.

### 4. Directory Structure

The following directories are required for the pipeline to work as expected:

- **`incoming_audio/`**: Place `.m4a` audio files here for processing.
- **`intermediate_transcripts/`**: Stores individual transcription files for each audio file.
- **`output/`**: Stores the final `transcripts.md` and `summary_action.md` files, with a date-time prefix for unique filenames.

You can customize the directory paths in the `.env` file.

## Usage

To run the pipeline, execute:

```bash
python main.py
```

### Workflow

1. **Transcription**: The script converts `.m4a` files to `.wav` and transcribes them using AssemblyAI. Transcriptions are saved in `intermediate_transcripts/`.
2. **Consolidation**: Transcriptions are combined and saved as `total_transcript.md` in `intermediate_transcript/`.
3. **Summarization**: If `total_transcript.md` exists, it is used directly for summarization with OpenAI GPT-4 to create `summary_action.md`.
4. **Output**: The consolidated transcript and summary files are moved to `output/`, with the current date-time prefixed to each filename.

## Example File Structure

After running the script, before clean up, you might have a structure like this:

```plaintext
project_root/
├── incoming_audio/
│   ├── audio1.m4a
│   └── audio2.m4a
├── intermediate_transcripts/
│   ├── audio1.wav.md
│   ├── audio2.wav.md
│   └── total_transcript.md
├── output/
│   ├── 2023-10-10-14-30-transcripts.md
│   └── 2023-10-10-14-30-summary_action.md
└── main.py
```

## Notes

- Ensure `ffmpeg` is correctly installed and accessible in your system PATH for `pydub` to process `.m4a` files.
- Run the script in an environment with internet access, as it relies on external APIs (AssemblyAI and OpenAI).

## License

This project is licensed under the MIT License.
