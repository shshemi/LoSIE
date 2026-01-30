import argparse
import random
from pathlib import Path


def split_jsonl(
    input_file, output_dir, train_ratio, valid_ratio, test_ratio, seed=None
):
    """
    Split a JSONL file into train, valid, and test sets.

    Args:
        input_file: Path to input JSONL file
        output_dir: Directory to save split files
        train_ratio: Proportion for training set
        valid_ratio: Proportion for validation set
        test_ratio: Proportion for test set
        seed: Random seed for reproducibility
    """
    if seed is not None:
        random.seed(seed)

    # Validate ratios
    total_ratio = train_ratio + valid_ratio + test_ratio
    if not (0.99 <= total_ratio <= 1.01):
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Read all lines from input file
    lines = []
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    # Shuffle lines
    random.shuffle(lines)

    # Calculate split indices
    total_lines = len(lines)
    train_count = int(total_lines * train_ratio)
    valid_count = int(total_lines * valid_ratio)

    train_lines = lines[:train_count]
    valid_lines = lines[train_count : train_count + valid_count]
    test_lines = lines[train_count + valid_count :]

    # Write split files
    with open(output_path / "train.jsonl", "w") as f:
        for line in train_lines:
            f.write(line + "\n")

    with open(output_path / "valid.jsonl", "w") as f:
        for line in valid_lines:
            f.write(line + "\n")

    with open(output_path / "test.jsonl", "w") as f:
        for line in test_lines:
            f.write(line + "\n")

    print("Split complete!")
    print(f"Total lines: {total_lines}")
    print(f"Train: {len(train_lines)} ({len(train_lines) / total_lines * 100:.1f}%)")
    print(f"Valid: {len(valid_lines)} ({len(valid_lines) / total_lines * 100:.1f}%)")
    print(f"Test: {len(test_lines)} ({len(test_lines) / total_lines * 100:.1f}%)")
    print(f"Output files saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Split JSONL file into train, valid, and test sets"
    )
    parser.add_argument("input_file", help="Path to input JSONL file")
    parser.add_argument(
        "-o",
        "--output_dir",
        default="./splits",
        help="Output directory for split files (default: ./splits)",
    )
    parser.add_argument(
        "-t",
        "--train_ratio",
        type=float,
        default=0.8,
        help="Training set ratio (default: 0.8)",
    )
    parser.add_argument(
        "-v",
        "--valid_ratio",
        type=float,
        default=0.1,
        help="Validation set ratio (default: 0.1)",
    )
    parser.add_argument(
        "--test_ratio", type=float, default=0.1, help="Test set ratio (default: 0.1)"
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=None, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    try:
        split_jsonl(
            args.input_file,
            args.output_dir,
            args.train_ratio,
            args.valid_ratio,
            args.test_ratio,
            args.seed,
        )
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
