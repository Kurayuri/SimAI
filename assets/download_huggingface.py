from huggingface_hub import snapshot_download
import os

# 模型ID（示例）
repo_id = "deepseek-ai/DeepSeek-V3-0324"

# 获取仓库文件列表，排除模型参数文件
ignore_patterns = ["*.bin", "*.safetensors", "*model*.bin", "*model*.safetensors"]

# 下载非模型参数文件
downloaded_path = snapshot_download(
    repo_id=repo_id,
    ignore_patterns=ignore_patterns,  # 排除模型参数
    local_dir=repo_id,
)

print(f"文件已下载到: {downloaded_path}")