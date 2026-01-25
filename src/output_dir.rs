use std::{
    fs,
    path::{Path, PathBuf},
};

#[derive(Debug, Clone)]
pub struct OutputDir {
    dir: PathBuf,
}

impl OutputDir {
    pub fn file_with_name(&self, name: impl AsRef<Path>) -> PathBuf {
        self.dir.join(name).with_extension("log")
    }
}

impl Default for OutputDir {
    fn default() -> Self {
        let dir = PathBuf::from("output").join(format!(
            "{}",
            chrono::Utc::now().format("%d-%m-%Y %H:%M:%S")
        ));
        fs::create_dir_all(&dir).unwrap();
        Self { dir }
    }
}
