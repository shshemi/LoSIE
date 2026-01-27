use std::path::PathBuf;

use genai::{
    Client,
    chat::{ChatMessage, ChatRequest},
};
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use tokio::fs::read_to_string;

use crate::{AppResult, token_bucket::TokenBucket};

pub async fn generate_target(
    files: Vec<PathBuf>,
    out: Option<PathBuf>,
    model: String,
) -> AppResult<()> {
    let client = Client::builder().build();
    let tb = TokenBucket::new(64);
    for path in files {
        for line in read_to_string(path).await?.lines() {
            let model = model.clone();
            let without_target = serde_json::from_str(line)?;
            let client = client.clone();
            tb.send(async move {
                let prompt = build_prompt(&without_target);
                let res = client
                    .exec_chat(
                        &model,
                        ChatRequest::new(vec![ChatMessage::user(prompt)]),
                        None,
                    )
                    .await;
                let target = res
                    .ok()
                    .and_then(|cr| cr.into_first_text())
                    .unwrap_or_default();
                without_target.into_with_target(target)
            });
        }
    }
    let contents = tb
        .into_iter()
        .filter_map(|with_target| serde_json::to_string(&with_target).ok())
        .join("\n");

    if let Some(path) = out {
        tokio::fs::write(path, contents).await?;
    } else {
        println!("{contents}");
    }

    Ok(())
}

#[derive(Debug, Deserialize)]
struct LogLineWithoutTarget {
    source: String,
    text: String,
}

impl LogLineWithoutTarget {
    fn into_with_target(self, target: String) -> LogLineWithTarget {
        LogLineWithTarget {
            source: self.source,
            text: self.text,
            target,
        }
    }
}

#[derive(Debug, Serialize)]
struct LogLineWithTarget {
    source: String,
    text: String,
    target: String,
}

fn build_prompt(log: &LogLineWithoutTarget) -> String {
    format!(
        "Your task it to extract information in key value format from log lines.\
Analyze the line carefully sandwiched in triple backticks. Then produce\
the key value information. After key values, generate one pair with key\
'@' and the value the shows a up to five words summary of the log content. Then, write\
the output in the following format:
Key1 Value1
Key2 Value2
@ Summary
Keep in mind that keys should not contain any whitespace characters, and \
key are separated from value by a space. Furthermore, key-value pairs are\
separated from each other by a new line character.
Now produce key-values for the following line of log
```
{}
```
Keep in mind that this log is generated from the software {}. So, produce\
the key-values with respect to that software. Do not write anything other\
than the key values. Just print the key-values and summary",
        log.text, log.source
    )
}
