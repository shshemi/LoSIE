def main():
    from transformers import pipeline

    pipe = pipeline(
        # task="summarization",  # or "translation", etc., depending on your task
        task="translation",  # or "translation", etc., depending on your task
        model="./autotrain-seq2seq-local",
        tokenizer="./autotrain-seq2seq-local",
        max_length=2**14,
    )

    line = '1991-02-14T03:12:09Z knotd[112:7]: debug: cache: prefetch worker started (view=\"default\", max_items=512)'
    result = pipe(line)
    assert isinstance(result, list)
    print(line)
    print(result[0]["translation_text"])
    # for line in result[0]["translation_text"].splitlines():
    #     key, value = line.split(maxsplit=2)
    #     print(key, value)
    # print(result)


if __name__ == "__main__":
    main()
