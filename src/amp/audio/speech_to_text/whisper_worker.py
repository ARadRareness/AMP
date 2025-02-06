import json
import os
from faster_whisper import WhisperModel

# load env
from dotenv import load_dotenv

load_dotenv()


# Fix for unload crash, see https://github.com/SYSTRAN/faster-whisper/issues/71 for more information
def transcribe(filepath, output_file, language="en"):
    try:
        model_name = os.getenv("AUDIO.WHISPER_MODEL", "base.en")
        model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")

        with open("whisper.log", "a") as log_file:
            log_file.write(f"Starting transcription of {filepath}\n")

        try:
            segments, info = model.transcribe(
                filepath,
                beam_size=5,
                # initial_prompt="DEFAULT",
                language=language,
                vad_filter=True,
                word_timestamps=True,
            )
        except IndexError:  # Handle tuple index out of range
            with open("whisper.log", "a") as log_file:
                log_file.write(
                    f"Error processing {filepath}: tuple index out of range\n"
                )
            result = {"segments": [], "info": {"language": language}}
        else:
            with open("whisper.log", "a") as log_file:
                log_file.write(
                    f"Transcription completed for {filepath}, creating result dict\n"
                )

            result = {
                "segments": [
                    {"text": s.text, "start": s.start, "end": s.end} for s in segments
                ],
                "info": info._asdict(),
            }

        with open("whisper.log", "a") as log_file:
            log_file.write(f"Writing results to {output_file}\n")

        with open(output_file, "w") as f:
            json.dump(result, f)

    except Exception as e:
        error_message = f"Error processing {filepath}: {str(e)}\n"
        with open("whisper.log", "a") as log_file:
            log_file.write(error_message)
        raise


def test_transcribe_to_srt(filepath):
    import whisper_manager

    json_file = filepath + ".json"

    whisper = whisper_manager.WhisperManager()

    transcribe(filepath, json_file, "en")
    with open(json_file, "r") as f:
        result_data = json.load(f)
    os.remove(json_file)

    srt_output = whisper.generate_srt(result_data["segments"])
    with open(filepath + ".srt", "w") as f:
        f.write(srt_output)


def separate_voice_from_audio(filepath):
    import demucs.separate

    demucs.separate.main(
        [
            "--mp3",
            "--two-stems",
            "vocals",
            "--segment",
            "10",
            "-n",
            "hdemucs_mmi",
            filepath,
        ]
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        filepath = "E:\\test\\vocals.mp4"
        # separate_voice_from_audio(filepath)
        test_transcribe_to_srt(filepath)
    else:
        filepath, output_file = sys.argv[1:3]
        transcribe(filepath, output_file)
