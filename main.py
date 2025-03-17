import json
import os
import tempfile

import requests
from dotenv import load_dotenv
from moviepy import (
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)
from murf import Murf
from openai import OpenAI

load_dotenv()


PROMPT = """
You are an automated system that helps generate 8-second videos. The user will provide a
prompt, based on which, you will return a script. Each sentence of the script will be an
object in the array. 

The object will have the following attributes:

* text - the sentence of the script. 

* image - a prompt that can be sent to DALL-E to generate the perfect,
photorealistic image for the given sentence that also aligns with the overall context
of the video; the image should have little or no text in it. 

* voice - a voice id that will be used by a TTS service; Only one voice should be used
per video; For documentary videos, use en-UK-gabriel; for promo, ad-like videos, or any
video with happy vibes, use en-UK-reggie for British accent or en-US-caleb for American
accent; for informational videos like tutorials or lessons, use en-UK-hazel or en-US-miles;
for other generic or general videos, use en-US-miles.
"""


def generate_script(client: OpenAI, prompt: str) -> str:
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "system", "content": PROMPT},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "script",
                "schema": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "image": {"type": "string"},
                                    "voice": {"type": "string"},
                                },
                                "required": ["text", "image", "voice"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["scenes"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    )

    return json.loads(response.output_text)


def generate_image(client: OpenAI, prompt: str) -> str:
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url


def generate_voiceover(client: Murf, voice: str, text: str) -> str:
    response = client.text_to_speech.generate(
        text=text,
        voice_id=voice,
    )

    return response.audio_file


def download_file(url: str, path: str) -> None:
    response = requests.get(url)
    with open(path, "wb") as f:
        f.write(response.content)


def generate_video(movie: list[dict]) -> str:
    clips = []
    for index, scene in enumerate(movie):
        image_url = scene["image"]
        voiceover_url = scene["voiceover"]

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, f"scene_{index}.png")
            download_file(image_url, image_path)

            voiceover_path = os.path.join(temp_dir, f"scene_{index}.wav")
            download_file(voiceover_url, voiceover_path)

            audio_clip = AudioFileClip(voiceover_path)
            video_clip = ImageClip(image_path, duration=(int(audio_clip.duration) + 1))
            video_clip = video_clip.with_audio(audio_clip)
            clips.append(video_clip)

    final_video = concatenate_videoclips(clips)
    final_video.write_videofile("video.mp4", fps=24, codec="libx264")
    final_video.close()


def main():
    client = OpenAI()
    murf_client = Murf()

    script = generate_script(client, "A bedtime story about a unicorn.")

    movie = []

    for scene in script["scenes"]:
        image_url = generate_image(client, scene["image"])
        voiceover_url = generate_voiceover(murf_client, scene["voice"], scene["text"])
        movie.append(
            {
                "image": image_url,
                "voiceover": voiceover_url,
            }
        )

    generate_video(movie)


if __name__ == "__main__":
    main()
