import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Process input and output files")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("output_file", help="Path to the output file")

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file

    with open(output_file, "w") as wfp:
        with open(input_file, "r") as rfp:
            for line in rfp:
                obj = json.loads(line)
                text = obj["text"]
                target = obj["target"]
                for tl in target.split("\n"):
                    key, value = tl.split(" ", maxsplit=1)
                    if key != "@":
                        obj = {"text": f"{text} <extra_id_99> {value}", "target": key}
                        wfp.write(f"{json.dumps(obj)}\n")


if __name__ == "__main__":
    main()
