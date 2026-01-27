use std::sync::Arc;

use clap::Parser;
use ler_datagen::{AppResult, cli_args::CliArgs, gentar, synlog};

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
