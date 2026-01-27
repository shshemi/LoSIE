use std::sync::Arc;

use std::path::PathBuf;

use clap::Parser;
use ler_datagen::{AppResult, gentar, synlog};

#[derive(Parser, Debug)]
#[command(
    name = "lie",
    version,
    about = "Data generation tool for log information extraction"
)]
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
        #[arg(short, long, required = false)]
        out: Option<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(short, long, required = false, default_value_t = String::from("gpt-5-mini-2025-08-07"))]
        model: String,

        #[arg(short, long, required = false, default_value_t = 10)]
        count: usize,
    },
    Gentar {
        /// Files
        #[arg(required = true)]
        files: Vec<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(short, long, required = false)]
        out: Option<PathBuf>,

        /// The output file, otherwise stdout
        #[arg(short, long, required = false, default_value_t = String::from("gpt-5-mini-2025-08-07"))]
        model: String,
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
        } => synlog::synthetize_log(sources, file, out, count, Arc::from(model)).await?,
        CliArgs::Gentar { files, out, model } => gentar::generate_target(files, out, model).await?,
    };
    Ok(())
}
