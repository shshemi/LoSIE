use std::{path::PathBuf, sync::Arc};

use genai::{
    ClientBuilder,
    chat::{ChatMessage, ChatRequest},
};
use serde::Serialize;

use crate::{AppResult, token_bucket::TokenBucket};

pub async fn synthetize_log(
    mut sources: Vec<String>,
    file: Option<PathBuf>,
    out: Option<PathBuf>,
    count: usize,
    model: Arc<str>,
) -> AppResult<()> {
    if let Some(path) = file {
        tokio::fs::read_to_string(path)
            .await?
            .lines()
            .for_each(|l| {
                sources.push(l.to_owned());
            });
    }
    let client = ClientBuilder::default().build();
    let tb = TokenBucket::new(64);

    for src in sources {
        let src = src.clone();
        let prompt = build_prompt(&src, count);
        let client = client.clone();
        let model = model.clone();
        tb.send(async move {
            (
                src,
                client
                    .exec_chat(
                        &model,
                        ChatRequest::new(vec![ChatMessage::user(prompt)]),
                        None,
                    )
                    .await,
            )
        });
    }

    let mut contents = String::new();
    for (src, res) in tb {
        let cr = res?;
        for text in cr.texts() {
            for line in text.lines() {
                if !line.is_empty() {
                    let json = serde_json::to_string(&LogLine {
                        source: &src,
                        text: line,
                    })?;
                    contents.push_str(&json);
                    contents.push('\n');
                }
            }
        }
    }
    if let Some(path) = out {
        tokio::fs::write(path, contents).await?;
    } else {
        println!("{contents}")
    }
    Ok(())
}

fn build_prompt(name: &str, count: usize) -> String {
    format!("
Log lines are semi-structured line delimitered texts\
produces by software during its runtime that repots the\
occurance of an event or and internal state in the\
software. Your task is to generate synthetic logs\
with the following EXTREEMLY IMPORTANT properties:
- Synthetic logs should resemble log produced by {name}.
- All the output in plain text.
- Do not produce any markdown or any other formatting, just the plain text.
- Use all possible log templates available for {name}.
- Use logs from different capabilities of {name}
- Use all possible log levels for this software.
- Use all possible app related loggers that you are aware.
- Uniformly distribute log timestamps across various years (from 1990-2050), months, days, and time of the day.
Now with all the previous criteria in mind, generate {count} samples.
    ")
}

#[derive(Debug, Serialize)]
struct LogLine<'a, 'b> {
    source: &'a str,
    text: &'b str,
}
