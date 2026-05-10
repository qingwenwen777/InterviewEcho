import asyncio
import sys
import os
import time

# Add current directory to path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    import sounddevice as sd
    from scipy.io.wavfile import write
    import numpy as np
except ImportError:
    print("\n[!] 缺失必要库。请先运行: pip install sounddevice scipy numpy")
    sys.exit(1)

from services.stt_service import stt_service
from core.llm_service import polish_text

async def record_audio(duration=5, fs=16000, filename="live_test.wav"):
    """
    使用 sounddevice 录制指定时长的音频
    """
    print(f"\n>>> 准备就绪！录音时长设定为 {duration} 秒。")
    print(">>> 请在看到 '开始录音' 后说话...")
    time.sleep(1)
    
    print("\n🔴 [开始录音] 请说话...")
    # 录制音频
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    
    # 显示倒计时进度条
    for i in range(duration, 0, -1):
        sys.stdout.write(f"\r还剩 {i} 秒... {'#' * i}")
        sys.stdout.flush()
        time.sleep(1)
    
    sd.wait()  # 等待录音结束
    print("\n🟢 [录音结束] 正在保存并处理数据...")
    
    # 转换为 int16 格式以便保存为标准 wav
    # 乘以 32767 将 float32 [-1.0, 1.0] 转换为 int16
    audio_int16 = (recording * 32767).astype(np.int16)
    write(filename, fs, audio_int16)
    return filename

async def main():
    # 获取参数：录音时长
    duration = 5
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            pass

    temp_file = "live_test.wav"

    try:
        # 1. 现场录音
        await record_audio(duration, filename=temp_file)

        # 2. 识别
        print("\n[阶段 1] 正在通过本地 Whisper 模型进行识别...")
        raw_text = stt_service.transcribe(temp_file)
        
        if not raw_text:
            print("识别结果为空，请确保麦克风有声音输入。")
        else:
            print("-" * 30)
            print(f"【原始识别】: {raw_text}")
            print("-" * 30)

            # 3. LLM 修正
            print("\n[阶段 2] 正在通过 LLM (gpt-3.5-turbo-1106) 进行标点/拼写修正...")
            polished = await polish_text(raw_text)
            print("-" * 30)
            print(f"【修正结果】: {polished}")
            print("-" * 30)

    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n(已清理临时音频文件 {temp_file})")

if __name__ == "__main__":
    asyncio.run(main())
