use std::path::PathBuf;

use clap::Parser;
use data_gen::{AppResult, gentar, synlog};

#[derive(Parser, Debug)]
#[command(about = "A tool to generate data for structred infromation extraction")]
pub enum CliArgs {
    /// Synthetize log from given source(s)
    Synlog {
        /// Sources
        #[arg(required = false)]
        sources: Vec<String>,

        /// File containing the source name(s) seperated by newline
        #[arg(short, long, required = false)]
        file: Option<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(long, required = false)]
        out: Option<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(long, required = false, default_value_t = String::from("gpt-5-mini-2025-08-07"))]
        model: String,

        /// Number of lines generated for each source
        #[arg(long, required = false, default_value_t = 10)]
        count: usize,
    },
    /// Generate target (key-value information) for logs
    Gentar {
        /// Files
        #[arg(required = true)]
        files: Vec<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(short, long, required = false)]
        out: Option<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(long, required = false, default_value_t = String::from("gpt-5-mini-2025-08-07"))]
        model: String,

        /// The number of samples to skip before generating targets
        #[arg(long, required = false, default_value_t = 0)]
        skip: usize,

        /// The number of samples to generate target
        #[arg(long, required = false)]
        count: Option<usize>,

        /// The number parallel connections to the LLM provider
        #[arg(long, required = false, default_value_t = 128)]
        connections: usize,
    },
}

#[tokio::main]
async fn main() -> AppResult<()> {
    dotenvy::dotenv().ok();
    let cli_args = CliArgs::parse();
    match cli_args {
        CliArgs::Synlog {
            sources,
            file,
            out,
            model,
            count,
        } => synlog::exec(sources, file, out, count, model).await?,
        CliArgs::Gentar {
            files,
            out,
            model,
            skip,
            count,
            connections,
        } => gentar::exec(files, out, model, skip, count, connections).await?,
    };
    Ok(())
}
