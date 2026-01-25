use std::{fs::File, io::Write, path::Path};

use futures::StreamExt;
use genai::{
    Client, ClientBuilder,
    chat::{ChatMessage, ChatRequest},
};
use itertools::Itertools;
use ler_datagen::{AppResult, output_dir::OutputDir, parser::ParserExt};
use tokio::fs;
use tracing::{error, info};

const MODEL: &str = "gpt-5-mini-2025-08-07";

#[tokio::main]
async fn main() -> AppResult<()> {
    tracing_subscriber::fmt::init();
    dotenvy::dotenv().ok();
    // let client = ClientBuilder::default().build();
    // generate(&client).await;
    // tag(&client, "output/29-12-2025 14:38:44 - cleaned").await?;
    parse(&fs::read_to_string("output.txt").await?).await?;
    Ok(())
}

async fn parse(txt_contents: &str) -> AppResult<()> {
    let samples = txt_contents
        .samples()
        .map(|s| serde_json::to_string(&s))
        .collect::<Result<Vec<String>, _>>()?;
    // let file = File::create("output.json")?;
    // serde_json::to_writer(&file, &samples)?;
    // println!("{}", samples);
    let train = &samples[..15000];
    let valid = &samples[15000..];
    std::fs::write("train.jsonl", train.join("\n").as_str())?;
    std::fs::write("valid.jsonl", valid.join("\n").as_str())?;
    Ok(())
}

async fn tag(client: &Client, path: impl AsRef<Path>) -> AppResult<()> {
    let mut join_vec = Vec::new();
    for entry in std::fs::read_dir(&path)? {
        let entry = entry?;
        for (line_no, line) in fs::read_to_string(entry.path())
            .await?
            .lines()
            .enumerate()
            .filter(|(_, l)| !l.is_empty())
        {
            let log_line = line.trim().to_owned();
            let msg = format!(
                "Annotating [{}:{}]",
                entry
                    .path()
                    .file_name()
                    .unwrap_or_default()
                    .to_str()
                    .unwrap_or_default(),
                line_no
            );
            join_vec.push(async move {
                info!("{msg}");
                annotate(client, &log_line)
                    .await
                    .map(|annots| format!("{}\n{}\n\n", log_line, annots))
            });
        }
    }
    info!("{} lines are queued for tagging", join_vec.len());
    let contents = futures::stream::iter(join_vec)
        .buffered(128)
        .collect::<Vec<_>>()
        .await
        .into_iter()
        .filter_map(Result::ok)
        .collect::<String>();
    tokio::fs::write("output.txt", &contents).await?;
    Ok(())
}

async fn generate(client: &Client) {
    let output_dir = OutputDir::default();
    info!("Ouput dir created at {output_dir:?}",);
    let mut join_vec = Vec::new();
    for software_name in include_str!("../software_list.txt")
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
    // .skip(140)
    // .take(20)
    {
        let client = client.clone();
        let output_dir = output_dir.clone();
        join_vec.push(async move {
            info!("Generating logs for {software_name}");
            let path = output_dir.file_with_name(software_name);
            let logs = match synthesize_log(&client, software_name, 40).await {
                Ok(logs) => logs,
                Err(err) => {
                    error!("Generation for {software_name} failed with error:\n{}", err);
                    return;
                }
            };
            let line_count = logs.lines().count();
            match fs::write(&path, logs).await {
                Ok(_) => {
                    info!(
                        "{line_count} lines of log was generated an stored in {}",
                        path.to_str().unwrap_or("unknown")
                    );
                }
                Err(err) => {
                    error!("Generation for {software_name} failed with error:\n{}", err);
                }
            }
        });
    }
    futures::stream::iter(join_vec)
        .buffered(64)
        .collect::<Vec<_>>()
        .await;
}

async fn synthesize_log(client: &Client, software_name: &str, count: usize) -> AppResult<String> {
    single_prompt(client, format!("
Log lines are semi-structured line delimitered texts\
produces by software during its runtime that repots the\
occurance of an event or and internal state in the\
software. Your task is to generate synthetic logs\
with the following EXTREEMLY IMPORTANT properties:
- Synthetic logs should resemble log produced by {software_name}.
- All the output in plain text.
- Do not produce any markdown or any other formatting, just the plain text.
- Use all possible log templates available for {software_name}.
- Use logs from different capabilities of {software_name}
- Use all possible log levels for this software.
- Use all possible app related loggers that you are aware.
- Uniformly distribute log timestamps across various years (from 1990-2050), months, days, and time of the day.
Now with all the previous criteria in mind, generate {count} samples.
").as_str()).await
}

async fn annotate(client: &Client, log_line: &str) -> AppResult<String> {
    single_prompt(client, format!("Your task is to annotate the given line of log sandwiched between the\
        tiple backticks (```). In order to do that, first go throught the entire line and analyze it. Then, identify\
        the annotation pieces with respect to the available tags (tags will be provided to you). Then, prepare the\
        pairs of tags and their corresponding value in the log line. Then produce the output in the following format.\
        First write the tag then the value separated by a space, and write one and only one tag value per line like this:
        TAG1 VALUE1
        TAG2 VALUE2
        Here is a list of available tags and their description:
        LEVEL: Show how severe the the log message is, such as  `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, and ... in the header
        TIMESTAMP: The time of occurance of the log message usually at the begininig of the text `2025-11-24T10:15:32Z` in the header
        LOGGER: The name of the entity that is responsible for producing the log message in the header. It could be a the name of process in some systems, such as  `sshd` and `hadoop`, or a service, such as `AlarmManager`, `PowerManagerService`, or even a class, function, or a handler in the code, such as `actix_web::middleware::error`
        IP_ADDR: An IP address like `169.201.11.58` that is used to show a source or a destination of network operation in the log messages or header
        INET_ADDR: Combination of IP address and port like `192.168.1.1:8080` in the message or header
        URI: Universal Resource Identifier like `https://google.com` in the header or message
        REL_URL: A relative Universal Resource Location like `/product` in the header or message
        FILE_PATH: A file path like `/home/root/.cache/` in the header or message
        DOMAIN: A domain name `com.amap.android.ams` in the header or message
        DOMAIN_PORT: A combination of domain with a port in `com.amap.android.ams:8080` header or message that is usually used in networking applications to be as an address.
        FUNCTION: A function call like `jk2_init()` in the header or message
        ID: An indication of an internal ID variable like `blk_38865049064139660` or `NODE-32` in the header or message
        PROTOCOL: A well-known protocol such as `FTP`, `HTTPS`, or any other protocol in the header or message
        VERSION: A number, group of numbers, or a string which indicated a version like `1.0.12` or `LATEST` in the header or message

        Now analyze, find and produce tags for the following line of log:
        ```
        {log_line}
        ```
        ").as_str()).await
}

async fn single_prompt(client: &Client, prompt: &str) -> AppResult<String> {
    let res = client
        .exec_chat(
            MODEL,
            ChatRequest::new(vec![ChatMessage::user(prompt)]),
            None,
        )
        .await?;
    Ok(res.texts().into_iter().join("\n"))
}
