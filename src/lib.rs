pub mod cli_args;
pub mod output_dir;
pub mod parser;
pub mod synlog;
pub type AppResult<T> = anyhow::Result<T>;
