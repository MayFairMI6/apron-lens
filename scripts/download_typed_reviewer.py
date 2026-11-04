"""Fetch the pinned local typed-review classifier; never download executable code."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modelaccess.nli import MODEL_ID, MODEL_REVISION

def main():
    from huggingface_hub import snapshot_download
    path=snapshot_download(MODEL_ID,revision=MODEL_REVISION,
        allow_patterns=['model.safetensors','config.json','tokenizer.json',
                        'tokenizer_config.json','special_tokens_map.json',
                        'added_tokens.json','spm.model','README.md','LICENSE'],max_workers=3)
    print('Pinned typed-review classifier available:',path)

if __name__=='__main__':main()
