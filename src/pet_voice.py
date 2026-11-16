import os
import time
import tempfile
import threading
from gtts import gTTS

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    import audioop
    HAS_NUMPY = False


class PetVoiceManager:
    """管理桌寵語音合成與音量播放（支援向量化音量調整與防重疊機制）"""

    _play_lock = threading.Lock()
    _latest_speech_id = 0
    _id_lock = threading.Lock()

    @staticmethod
    def speak(pet, text: str):
        if not getattr(pet, "voice_enabled", True) or not text:
            return

        # 遞增語音序號，若同時觸發多句話，只保留最新的一句，避免排隊堆積
        with PetVoiceManager._id_lock:
            PetVoiceManager._latest_speech_id += 1
            speech_id = PetVoiceManager._latest_speech_id

        def run_tts():
            temp_filename = None
            device = None
            try:
                # 1. 下載 TTS 音檔（在拿到播放鎖之前先下載，節省等待時間）
                tts = gTTS(text=text, lang="zh-TW", slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)

                # 下載完後檢查：如果已經有更新的台詞插隊，直接放棄這句過時的語音
                with PetVoiceManager._id_lock:
                    if speech_id != PetVoiceManager._latest_speech_id:
                        return

                import miniaudio

                decoded = miniaudio.decode_file(
                    temp_filename,
                    output_format=miniaudio.SampleFormat.SIGNED16,
                    nchannels=2,
                    sample_rate=44100,
                )

                # 2. 取得播放鎖，確保同一時間只有一個聲音在播放（不重疊）
                with PetVoiceManager._play_lock:
                    # 再次檢查是否已被更新的台詞取代
                    with PetVoiceManager._id_lock:
                        if speech_id != PetVoiceManager._latest_speech_id:
                            return

                    current_volume = max(0.0, min(1.0, float(getattr(pet, "voice_volume", 0.8))))
                    if current_volume <= 0.0:
                        return

                    # 3. 向量化快速調整音量（取代原本慢速的 Python for 迴圈）
                    raw_bytes = bytes(decoded.samples)
                    if current_volume < 0.999:
                        if HAS_NUMPY:
                            samples = np.frombuffer(raw_bytes, dtype=np.int16)
                            scaled = np.clip(samples * current_volume, -32768, 32767).astype(np.int16)
                            pcm_bytes = scaled.tobytes()
                        else:
                            pcm_bytes = audioop.mul(raw_bytes, 2, current_volume)
                    else:
                        pcm_bytes = raw_bytes

                    frame_bytes = decoded.nchannels * 2
                    total_bytes = len(pcm_bytes)
                    done = threading.Event()

                    def pcm_generator():
                        pos = 0
                        required_frames = yield b""
                        while pos < total_bytes:
                            # 若播放途中被新語音打斷，提前結束播放
                            with PetVoiceManager._id_lock:
                                if speech_id != PetVoiceManager._latest_speech_id:
                                    break

                            num_frames = (
                                required_frames
                                if required_frames and required_frames > 0
                                else 1024
                            )
                            take_bytes = min(num_frames * frame_bytes, total_bytes - pos)
                            chunk = pcm_bytes[pos : pos + take_bytes]
                            pos += take_bytes
                            required_frames = yield chunk

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
                    time.sleep(0.1)

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
                        os.remove(temp_filename)
                    except Exception:
                        pass

        threading.Thread(target=run_tts, daemon=True).start()