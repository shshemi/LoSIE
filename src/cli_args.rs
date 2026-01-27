use std::path::PathBuf;

use clap::Parser;

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
