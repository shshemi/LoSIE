#!/usr/bin/env python3
"""Tests for unsloth/train.py — mocks GPU-dependent libraries."""
from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile
import yaml

# ---------------------------------------------------------------------------
# Stub out heavy dependencies before importing train.py
# ---------------------------------------------------------------------------

# unsloth
unsloth_mod = types.ModuleType("unsloth")
mock_flm = MagicMock(name="FastLanguageModel")
mock_model = MagicMock(name="model")
mock_tokenizer = MagicMock(name="tokenizer")
mock_flm.from_pretrained.return_value = (mock_model, mock_tokenizer)
mock_flm.get_peft_model.return_value = mock_model
unsloth_mod.FastLanguageModel = mock_flm
sys.modules["unsloth"] = unsloth_mod

# trl
trl_mod = types.ModuleType("trl")
mock_sft_config_cls = MagicMock(name="SFTConfig")
mock_sft_trainer_cls = MagicMock(name="SFTTrainer")
mock_trainer_instance = MagicMock(name="trainer_instance")
mock_sft_trainer_cls.return_value = mock_trainer_instance
trl_mod.SFTConfig = mock_sft_config_cls
trl_mod.SFTTrainer = mock_sft_trainer_cls
sys.modules["trl"] = trl_mod

# datasets
datasets_mod = types.ModuleType("datasets")
mock_load_dataset = MagicMock(name="load_dataset")
mock_dataset = {"train": [{"messages": []}], "valid": [{"messages": []}]}
mock_load_dataset.return_value = mock_dataset
datasets_mod.load_dataset = mock_load_dataset
sys.modules["datasets"] = datasets_mod

# Now import the module under test
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train  # noqa: E402


SAMPLE_CONFIG = {
    "task": "llm-sft",
    "base_model": "Qwen/Qwen3.5-0.8B",
    "project_name": "losie",
    "log": "tensorboard",
    "data": {
        "path": "/data",
        "train_split": "train",
        "valid_split": "valid",
        "chat_template": "tokenizer",
        "column_mapping": {"text_column": "messages"},
    },
    "params": {
        "block_size": 2048,
        "model_max_length": 4096,
        "epochs": 16,
        "batch_size": 128,
        "lr": 1e-5,
        "peft": True,
        "quantization": "int4",
        "target_modules": "all-linear",
        "padding": "right",
        "optimizer": "paged_adamw_8bit",
        "scheduler": "linear",
        "gradient_accumulation": 8,
        "mixed_precision": "bf16",
        "merge_adapter": True,
        "lora_r": 16,
        "lora_alpha": 16,
        "lora_dropout": 0,
    },
    "hub": {"username": "", "token": "", "push_to_hub": False},
}


class TestLoadConfig(unittest.TestCase):
    def test_load_config_parses_yaml(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            yaml.dump(SAMPLE_CONFIG, f)
            f.flush()
            cfg = train.load_config(f.name)
        self.assertEqual(cfg["base_model"], "Qwen/Qwen3.5-0.8B")
        self.assertEqual(cfg["params"]["lr"], 1e-5)


class TestMainWiring(unittest.TestCase):
    """Run main() with the sample config and assert correct calls."""

    def setUp(self):
        # Reset all mocks
        mock_flm.reset_mock()
        mock_sft_config_cls.reset_mock()
        mock_sft_trainer_cls.reset_mock()
        mock_trainer_instance.reset_mock()
        mock_load_dataset.reset_mock()
        mock_model.reset_mock()

        self.tmpfile = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False
        )
        yaml.dump(SAMPLE_CONFIG, self.tmpfile)
        self.tmpfile.flush()

    def _run_main(self):
        with patch("sys.argv", ["train.py", "--config", self.tmpfile.name]):
            train.main()

    # ---- model loading ----
    def test_from_pretrained_called_correctly(self):
        self._run_main()
        mock_flm.from_pretrained.assert_called_once_with(
            model_name="Qwen/Qwen3.5-0.8B",
            max_seq_length=4096,
            load_in_4bit=True,
        )

    def test_peft_model_params(self):
        self._run_main()
        mock_flm.get_peft_model.assert_called_once_with(
            mock_model,
            r=16,
            lora_alpha=16,
            lora_dropout=0,
            target_modules="all-linear",
            use_gradient_checkpointing="unsloth",
        )

    # ---- dataset loading ----
    def test_load_dataset_called(self):
        self._run_main()
        mock_load_dataset.assert_called_once_with(
            "json",
            data_dir="/data",
            data_files={"train": "train.jsonl", "valid": "valid.jsonl"},
        )

    # ---- SFTConfig mapping ----
    def test_sft_config_hyperparams(self):
        self._run_main()
        kw = mock_sft_config_cls.call_args
        self.assertEqual(kw.kwargs["per_device_train_batch_size"], 128)
        self.assertEqual(kw.kwargs["gradient_accumulation_steps"], 8)
        self.assertEqual(kw.kwargs["num_train_epochs"], 16)
        self.assertAlmostEqual(kw.kwargs["learning_rate"], 1e-5)
        self.assertTrue(kw.kwargs["bf16"])
        self.assertFalse(kw.kwargs["fp16"])
        self.assertEqual(kw.kwargs["optim"], "paged_adamw_8bit")
        self.assertEqual(kw.kwargs["lr_scheduler_type"], "linear")
        self.assertEqual(kw.kwargs["report_to"], "tensorboard")

    def test_sft_config_does_not_have_max_seq_length(self):
        """max_seq_length must NOT be in SFTConfig (bugfix #2)."""
        self._run_main()
        kw = mock_sft_config_cls.call_args
        self.assertNotIn("max_seq_length", kw.kwargs)

    # ---- SFTTrainer wiring ----
    def test_sft_trainer_receives_max_seq_length(self):
        """max_seq_length must be passed to SFTTrainer, not SFTConfig."""
        self._run_main()
        kw = mock_sft_trainer_cls.call_args
        self.assertEqual(kw.kwargs["max_seq_length"], 2048)

    def test_trainer_train_called(self):
        self._run_main()
        mock_trainer_instance.train.assert_called_once()

    # ---- merged save ----
    def test_save_pretrained_merged(self):
        self._run_main()
        mock_model.save_pretrained_merged.assert_called_once_with(
            "/output/losie/merged",
            tokenizer=mock_tokenizer,
            save_method="merged_16bit",
        )


class TestImportOrder(unittest.TestCase):
    """Verify unsloth is imported before trl/datasets (bugfix #1)."""

    def test_unsloth_imported_before_trl(self):
        src = Path(__file__).resolve().parent / "train.py"
        lines = src.read_text().splitlines()
        unsloth_line = next(
            i for i, l in enumerate(lines) if "from unsloth" in l
        )
        trl_line = next(i for i, l in enumerate(lines) if "from trl" in l)
        datasets_line = next(
            i for i, l in enumerate(lines) if "from datasets" in l
        )
        self.assertLess(
            unsloth_line, trl_line, "unsloth must be imported before trl"
        )
        self.assertLess(
            unsloth_line,
            datasets_line,
            "unsloth must be imported before datasets",
        )


if __name__ == "__main__":
    unittest.main()
