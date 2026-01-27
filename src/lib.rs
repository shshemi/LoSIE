pub mod cli_args;
pub mod output_dir;
pub mod parser;
pub mod synlog;
pub mod token_bucket;
pub type AppResult<T> = anyhow::Result<T>;
