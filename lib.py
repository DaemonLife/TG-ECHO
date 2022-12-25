#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence


# a function that splits the audio file into chunks
# and applies speech recognition
def get_large_audio_transcription(path, r):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """
    # open the audio file using pydub
    sound = AudioSegment.from_ogg(path)
    
    chunks = split_on_silence(sound,
        # default: 1000 The minimum length for silent sections in milliseconds.
        # If it is greater than the length of the audio segment an empty list will be returned.
        min_silence_len=700,
        # default: -16 The upper bound for how quiet is silent in dBFS.
        silence_thresh=-70,
        # default: 100 How much silence to keep in ms or a bool.
        # leave some silence at the beginning and end of the chunks.
        # Keeps the sound from sounding like it is abruptly cut off.
        # When the length of the silence is less than the keep_silence duration
        # it is split evenly between the preceding and following non-silent segments.
        # If True is specified, all the silence is kept, if False none is kept.
        keep_silence=100,
    )
    folder_name = "audio-chunks"
    whole_text = ""
    # process each chunk
    for i, audio_chunk in enumerate(chunks, start=1):
        # export audio chunk and save it in
        # the `folder_name` directory.
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        # recognize the chunk
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            # try converting it to text
            try:
                text = r.recognize_google(audio_listened, language="ru-RU")
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text
    # return the text for all chunks detected
    return whole_text


def main():
    pass


if __name__ == "__main__":
    try:
        main()
    except:
        print("Error on starting main function")

