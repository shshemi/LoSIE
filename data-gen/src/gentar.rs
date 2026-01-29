use std::{path::PathBuf, sync::Arc};

use genai::{
    Client,
    chat::{ChatMessage, ChatRequest},
};
use itertools::Itertools;
use serde::{Deserialize, Serialize};

use crate::{AppResult, token_bucket::AwaitInTokenBucket};

pub async fn exec(
    files: Vec<PathBuf>,
    out: Option<PathBuf>,
    model: impl Into<Arc<str>>,
    skip: usize,
    mut count: Option<usize>,
    connections: usize,
) -> AppResult<()> {
    let model = model.into();
    let client = Client::builder().build();
    let contents = files
        .iter()
        .map(|path| std::fs::read_to_string(path).unwrap())
        .join("\n")
        .lines()
        .filter_map(|line| serde_json::from_str::<WithoutTarget>(line).ok())
        .skip(skip)
        .take_while(|_| should_continue_decrementing(count.as_mut()))
        .map(|without_target| gen_target_with_llm(without_target, client.clone(), model.clone()))
        .await_in_token_bucket(connections)
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
struct WithoutTarget {
    source: String,
    text: String,
}

impl WithoutTarget {
    fn into_with_target(self, target: String) -> WithTarget {
        WithTarget {
            source: self.source,
            text: self.text,
            target,
        }
    }
}

#[derive(Debug, Serialize)]
struct WithTarget {
    source: String,
    text: String,
    target: String,
}

async fn gen_target_with_llm(
    without_target: WithoutTarget,
    client: Client,
    model: Arc<str>,
) -> WithTarget {
    let prompt = build_prompt(&without_target);
    let mut target = String::default();
    for _ in 0..5 {
        match client
            .exec_chat(
                &model,
                ChatRequest::new(vec![ChatMessage::user(&prompt)]),
                None,
            )
            .await
        {
            Ok(chat_request) => {
                if let Some(first_text) = chat_request.into_first_text() {
                    target = first_text;
                }
                break;
            }
            Err(err) => log::error!("Error: {err}"),
        }
    }
    without_target.into_with_target(target)
}

fn build_prompt(log: &WithoutTarget) -> String {
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

fn should_continue_decrementing(count: Option<&mut usize>) -> bool {
    match count {
        Some(0) => false,
        Some(c) => {
            *c = c.saturating_sub(1);
            true
        }
        None => true,
    }
}
