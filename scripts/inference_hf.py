# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "sentencepiece",
#     "tiktoken",
#     "transformers",
# ]
# ///

from transformers import AutoTokenizer, AutoModelForCausalLM


def main() -> None:

    # Path to your locally trained model
    MODEL_PATH = "output/losie/losie"
    SYSTEM_PROMPT = (
        "You are a log parser. Extract all key-value fields from the input log line, "
        "one per line, in the format: key value"
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    assert tokenizer is not None
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
    assert model is not None
    # Create the model
    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input.strip():
            continue

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        input_ids = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        )

        output_ids = model.generate(
            **input_ids,
            max_new_tokens=2048,
            # temperature=0.0,
            do_sample=False,
        )

        generated_ids = output_ids[0][input_ids["input_ids"].shape[1] :]
        print(tokenizer.decode(generated_ids, skip_special_tokens=True))

        # print(tokenizer.decode(output_ids, skip_special_tokens=True)[0])
        print()

    print("\nDone.")


if __name__ == "__main__":
    main()
