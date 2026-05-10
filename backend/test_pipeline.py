import asyncio
import sys
import os

# Add current directory to path so we can import modules correctly
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from services.stt_service import stt_service
from core.llm_service import polish_text

async def run_test_pipeline(audio_path):
    print("\n" + "="*50)
    print("InterviewEcho 语音识别 + LLM 纠错测试流水线")
    print("="*50)

    if not os.path.exists(audio_path):
        print(f"错误: 找不到音频文件 {audio_path}")
        return

    # 1. 运行 Whisper 识别
    print("\n[阶段 1] 运行 Whisper (Local) 识别中...")
    raw_text = stt_service.transcribe(audio_path)
    
    if not raw_text:
        print("识别失败，请检查音轨或 FFmpeg 是否正确安装。")
        return
    
    print("-" * 30)
    print(f"【原始转录结果】:\n{raw_text}")
    print("-" * 30)

    # 2. 运行 LLM 修正 (GPT-3.5-Turbo-1106)
    print("\n[阶段 2] 运行 LLM (Cloud) 修正与标点添加中...")
    polished_text = await polish_text(raw_text)
    
    print("-" * 30)
    print(f"【LLM 修正后结果】:\n{polished_text}")
    print("-" * 30)

    print("\n测试完成！")
    print("="*50)

if __name__ == "__main__":
    # 如果用户没有提供参数，则提示用法
    if len(sys.argv) < 2:
        print("使用方法: python test_pipeline.py <音频文件路径>")
        print("示例: python test_pipeline.py tests/sample_audio.wav")
    else:
        audio_file = sys.argv[1]
        asyncio.run(run_test_pipeline(audio_file))
