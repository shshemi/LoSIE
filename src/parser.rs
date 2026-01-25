use std::{iter::Enumerate, str::Lines};

use anyhow::anyhow;
use serde::{Deserialize, Serialize};

use crate::AppResult;

#[derive(Debug)]
pub struct Parser<'a> {
    lines: Enumerate<Lines<'a>>,
}

impl<'a> Iterator for Parser<'a> {
    type Item = Sample;

    fn next(&mut self) -> Option<Self::Item> {
        let mut state = State::Init;
        for (ln, line) in &mut self.lines {
            state = match state.next(line) {
                Ok(state) => state,
                Err(err) => panic!("Line {} : {}", ln + 1, err),
            };
            let sample = state.take_sample();
            if sample.is_some() {
                return sample;
            }
        }
        None
    }
}

enum State {
    Init,
    Text(String),
    TextWithSpans(String, Vec<String>),
    Finalized(Sample),
}

impl State {
    fn next(self, line: &str) -> AppResult<State> {
        match self {
            State::Init => Ok(if !line.is_empty() {
                State::Text(line.into())
            } else {
                State::Init
            }),
            State::Text(text) => {
                if text.is_empty() {
                    Ok(State::Init)
                } else if let Some((_, _)) = line.split_once(' ') {
                    let items = vec![line.to_owned()];
                    Ok(State::TextWithSpans(text, items))
                } else {
                    Err(anyhow!("Invalid annotation line"))
                }
            }
            State::TextWithSpans(text, mut items) => {
                if line.is_empty() {
                    Ok(State::Finalized(Sample {
                        input: text,
                        target: items.join("\n"),
                    }))
                } else if let Some((tag, slice)) = line.split_once(' ') {
                    items.push(line.to_owned());
                    Ok(State::TextWithSpans(text, items))
                } else {
                    Err(anyhow!("Invalid annotation line"))
                }
            }
            State::Finalized(sample) => {
                if !line.is_empty() {
                    Ok(State::Finalized(sample))
                } else {
                    Err(anyhow!("Produced sample not used"))
                }
            }
        }
    }

    fn take_sample(&mut self) -> Option<Sample> {
        match self {
            State::Finalized(sample) => {
                let sample = std::mem::take(sample);
                *self = State::Init;
                Some(sample)
            }
            _ => None,
        }
    }
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct Sample {
    input: String,
    target: String,
}

// #[derive(Debug, Default, Clone, Serialize, Deserialize)]
// pub struct Data {
//     text: String,
// }

// #[derive(Debug, Default, Clone, Serialize, Deserialize)]
// pub struct Prediction {
//     result: Vec<Result>,
// }

// #[derive(Debug, Default, Clone, Serialize, Deserialize)]
// pub struct Result {
//     from_name: String,
//     to_name: String,
//     r#type: String,
//     origin: String,
//     value: Value,
// }

// #[derive(Debug, Default, Clone, Serialize, Deserialize)]
// pub struct Value {
//     start: usize,
//     end: usize,
//     text: String,
//     labels: [String; 1],
// }

pub trait ParserExt {
    fn samples<'a>(&'a self) -> Parser<'a>;
}

impl ParserExt for str {
    fn samples<'a>(&'a self) -> Parser<'a> {
        Parser {
            lines: self.lines().enumerate(),
        }
    }
}
