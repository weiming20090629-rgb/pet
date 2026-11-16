import os
import time
import array
import tempfile
import threading
from gtts import gTTS


class PetVoiceManager:
    """管理桌寵語音合成與音量播放"""

    @staticmethod
    def speak(pet, text: str):
        if not getattr(pet, "voice_enabled", True) or not text:
            return

        current_volume = getattr(pet, "voice_volume", 0.8)

        def run_tts():
            temp_filename = None
            device = None
            try:
                tts = gTTS(text=text, lang="zh-TW", slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)

                import miniaudio

                decoded = miniaudio.decode_file(
                    temp_filename,
                    output_format=miniaudio.SampleFormat.SIGNED16,
                    nchannels=2,
                    sample_rate=44100,
                )

                samples = array.array("h", decoded.samples)
                for i in range(len(samples)):
                    val = int(samples[i] * current_volume)
                    samples[i] = max(-32768, min(32767, val))

                pcm_bytes = samples.tobytes()
                total_frames = len(samples) // decoded.nchannels
                frame_bytes = decoded.nchannels * 2
                done = threading.Event()

                def pcm_generator():
                    pos = 0
                    required_frames = yield b""
                    while pos < total_frames:
                        num_frames = required_frames if required_frames and required_frames > 0 else 1024
                        take = min(num_frames, total_frames - pos)
                        start_byte = pos * frame_bytes
                        end_byte = start_byte + take * frame_bytes
                        pos += take
                        required_frames = yield pcm_bytes[start_byte:end_byte]

                    done.set()
                    while True:
                        yield b""

                device = miniaudio.PlaybackDevice(
                    output_format=decoded.sample_format,
                    nchannels=decoded.nchannels,
                    sample_rate=decoded.sample_rate,
                )
                gen = pcm_generator()
                next(gen)
                device.start(gen)
                done.wait(timeout=30)
                time.sleep(0.2)
            except Exception as e:
                print(f"語音播放失敗: {e}")
            finally:
                if device is not None:
                    try:
                        device.stop()
                        device.close()
                    except Exception:
                        pass
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        time.sleep(0.2)
                        os.remove(temp_filename)
                    except Exception:
                        pass

        threading.Thread(target=run_tts, daemon=True).start()