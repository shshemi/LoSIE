use std::path::PathBuf;

use clap::{Parser, ValueEnum};

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
        #[arg(short, long, required = false)]
        model: Option<String>,

        #[arg(short, long, required = false, default_value_t = 5)]
        count: usize,
    },
}

#[derive(ValueEnum, Clone, Debug)]
pub enum Level {
    Low,
    Medium,
    High,
}
