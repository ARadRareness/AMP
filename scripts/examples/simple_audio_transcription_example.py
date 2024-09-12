import os
from amp_lib import AmpClient

amp = AmpClient()


# SRT mode
print(
    amp.speech_to_text(
        os.path.join(os.path.dirname(__file__), "audio", "example_audio.wav"),
        srt_mode=True,
    )
)

print("-" * 100)

# Normal mode
print(
    amp.speech_to_text(
        os.path.join(os.path.dirname(__file__), "audio", "example_audio.wav"),
        srt_mode=False,
    )
)
