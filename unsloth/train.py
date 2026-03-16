#!/usr/bin/env python3
"""Unsloth-based LoRA/QLoRA fine-tuning script for LLM-SFT."""

from __future__ import annotations

import argparse
import os

from unsloth import FastLanguageModel  # must be first
import yaml
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune with Unsloth")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML config file",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    params = cfg["params"]
    data_cfg = cfg["data"]

    max_seq_length = params.get("model_max_length", 4096)
    lora_r = params.get("lora_r", 16)
    lora_alpha = params.get("lora_alpha", 16)
    lora_dropout = params.get("lora_dropout", 0)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["base_model"],
        max_seq_length=max_seq_length,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules="all-linear",
        use_gradient_checkpointing="unsloth",
    )

    dataset = load_dataset(
        "json",
        data_dir=data_cfg["path"],
        data_files={
            "train": f"{data_cfg['train_split']}.jsonl",
            "valid": f"{data_cfg['valid_split']}.jsonl",
        },
    )

    def formatting_func(example):
        return [
            tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False
            )
            for msgs in example["messages"]
        ]

    mixed_precision = params.get("mixed_precision", "bf16")
    output_dir = f"/output/{cfg.get('project_name', 'losie')}"

    os.environ["TENSORBOARD_LOGGING_DIR"] = f"{output_dir}/logs"

    training_config = SFTConfig(
        output_dir=output_dir,
        per_device_train_batch_size=params.get("batch_size", 128),
        gradient_accumulation_steps=params.get("gradient_accumulation", 8),
        num_train_epochs=params.get("epochs", 16),
        learning_rate=float(params.get("lr", 1e-5)),
        bf16=mixed_precision == "bf16",
        fp16=mixed_precision == "fp16",
        optim=params.get("optimizer", "paged_adamw_8bit"),
        lr_scheduler_type=params.get("scheduler", "linear"),
        report_to=cfg.get("log", "tensorboard"),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["valid"],
        formatting_func=formatting_func,
        max_seq_length=params.get("block_size", 2048),
        args=training_config,
    )

    trainer.train()

    model.save_pretrained_merged(
        f"{output_dir}/merged", tokenizer=tokenizer, save_method="merged_16bit"
    )

    model.save_pretrained_gguf(
        f"{output_dir}/gguf", tokenizer=tokenizer, quantization_method="q4_k_m"
    )

    model.save_pretrained_gguf(
        f"{output_dir}/gguf", tokenizer=tokenizer, quantization_method="q8_0"
    )


if __name__ == "__main__":
    main()
