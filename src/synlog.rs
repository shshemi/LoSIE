use std::path::PathBuf;

use genai::{
    ClientBuilder,
    chat::{ChatMessage, ChatRequest},
};
use itertools::Itertools;
use serde::Serialize;

use crate::AppResult;

const MODEL: &str = "gpt-5-mini-2025-08-07";

pub async fn synthetize_log(
    mut sources: Vec<String>,
    file: Option<PathBuf>,
    out: Option<PathBuf>,
    count: usize,
    model: Option<String>,
) -> AppResult<()> {
    if let Some(path) = file {
        tokio::fs::read_to_string(path)
            .await?
            .lines()
            .for_each(|l| {
                sources.push(l.to_owned());
            });
    }
    println!("Synthetizing {count} log for {}", sources.iter().join(", "));
    let client = ClientBuilder::default().build();
    for src in sources {
        let prompt = build_prompt(&src, count);
        let contents = client
            .exec_chat(
                model.as_deref().unwrap_or(MODEL),
                ChatRequest::new(vec![ChatMessage::user(prompt)]),
                None,
            )
            .await?
            .texts()
            .into_iter()
            .flat_map(|text| text.lines())
            .filter(|line| !line.is_empty())
            .map(|line| LogLine {
                source: &src,
                text: line,
            })
            .map(|ll| serde_json::to_string(&ll))
            .collect::<Result<Vec<_>, _>>()?
            .join("\n");
        if let Some(path) = &out {
            let _ = tokio::fs::write(path, contents).await;
        } else {
            println!("{contents}");
        }
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
