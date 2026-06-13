"""
QLoRA fine-tune for StrykeX equity backtesting assistant.

Requires GPU (16GB+ VRAM recommended for 7B 4-bit) and:
  pip install -r training/requirements-train.txt

Usage:
  cd training
  python scripts/prepare_production_dataset.py --from-db
  python scripts/train_qlora.py
  python scripts/train_qlora.py --epochs 1 --max-samples 500   # smoke test

After training, merge and serve with Ollama:
  ollama create strykex-quant -f Modelfile
  # set LLM_MODEL_NAME=strykex-quant in .env
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="../configs/qlora_config.yaml")
    parser.add_argument("--train-file", default="../data/qa_pairs/strykex_backtest_train.jsonl")
    parser.add_argument("--eval-file", default="../data/qa_pairs/strykex_backtest_eval.jsonl")
    parser.add_argument("--output-dir", default="../outputs/strykex-qlora")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--max-samples", type=int, default=0, help="Limit rows for smoke test")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    cfg = load_config(root / args.config)
    train_path = root / args.train_file
    eval_path = root / args.eval_file
    output_dir = root / args.output_dir

    if not train_path.exists():
        raise SystemExit(f"Missing {train_path}. Run: python scripts/prepare_production_dataset.py --from-db")

    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import SFTTrainer
    except ImportError as e:
        raise SystemExit(
            "Install training deps: pip install -r training/requirements-train.txt\n" f"Missing: {e}"
        ) from e

    model_name = cfg["model"]["base"]
    epochs = args.epochs or cfg["training"]["epochs"]

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["alpha"],
        lora_dropout=cfg["lora"]["dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    def load_jsonl(path: Path):
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        return rows

    train_rows = load_jsonl(train_path)
    eval_rows = load_jsonl(eval_path) if eval_path.exists() else []
    if args.max_samples:
        train_rows = train_rows[: args.max_samples]
        eval_rows = eval_rows[: max(10, args.max_samples // 10)]

    def format_example(row: dict) -> str:
        parts = []
        for msg in row["messages"]:
            role = msg["role"].upper()
            parts.append(f"<|{role}|>\n{msg['content']}")
        parts.append("<|END|>")
        return "\n".join(parts)

    raw_train = load_dataset("json", data_files=str(train_path), split="train")
    train_ds = raw_train.map(lambda x: {"text": format_example(x)}, remove_columns=raw_train.column_names)

    eval_ds = None
    if eval_path.exists() and eval_rows:
        raw_eval = load_dataset("json", data_files=str(eval_path), split="train")
        eval_ds = raw_eval.map(lambda x: {"text": format_example(x)}, remove_columns=raw_eval.column_names)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=cfg["training"]["batch_size"],
        gradient_accumulation_steps=cfg["training"]["gradient_accumulation"],
        learning_rate=float(cfg["training"]["learning_rate"]),
        warmup_ratio=float(cfg["training"]["warmup_ratio"]),
        logging_steps=10,
        save_steps=200,
        eval_strategy="steps" if eval_ds else "no",
        eval_steps=200 if eval_ds else None,
        bf16=torch.cuda.is_available(),
        report_to="none",
        optim=cfg["training"].get("optimizer", "paged_adamw_8bit"),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=training_args,
        max_seq_length=cfg["training"]["max_seq_length"],
        dataset_text_field="text",
    )

    print(f"Training {model_name} on {len(train_rows)} samples -> {output_dir}")
    trainer.train()
    trainer.save_model(str(output_dir / "adapter"))
    tokenizer.save_pretrained(str(output_dir / "adapter"))
    print(f"Saved LoRA adapter to {output_dir / 'adapter'}")
    print("Next: merge adapter to GGUF and `ollama create strykex-quant -f Modelfile`")


if __name__ == "__main__":
    main()
