# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "transformers",
#     "vllm",
# ]
# ///

from vllm import LLM, SamplingParams


def main() -> None:

    # Path to your locally trained model
    MODEL_PATH = "output/losie/losie"

    # Create the model
    llm = LLM(model=MODEL_PATH, disable_sliding_window=True, max_model_len=4096)

    # Generation parameters
    sampling_params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=128)

    # Input prompts
    prompts = [
        "Explain what a transformer model is.",
        "Write a short poem about Rust programming.",
    ]

    # Run inference
    outputs = llm.generate(prompts, sampling_params)

    # Print results
    for output in outputs:
        prompt = output.prompt
        text = output.outputs[0].text
        print(f"Prompt: {prompt}")
        print(f"Completion: {text}")
        print("-" * 40)


if __name__ == "__main__":
    main()
