use itertools::Itertools;
use std::{
    pin::Pin,
    sync::{
        Arc,
        mpsc::{Receiver, Sender, channel},
    },
};
use tokio::{runtime::Runtime, sync::Semaphore};

use crate::AppResult;

type SendType<T> = Pin<Box<dyn Future<Output = T> + 'static + Send>>;
pub struct TokenBucket<T> {
    send: Sender<SendType<T>>,
    recv: Receiver<T>,
}

impl<T> TokenBucket<T>
where
    T: Send + 'static,
{
    pub fn new(tokens: usize) -> TokenBucket<T> {
        let (send, b_recv) = channel();
        let (b_send, recv) = channel();
        std::thread::spawn(move || {
            let sema = Arc::new(Semaphore::new(tokens));
            let rt = Runtime::new().unwrap();

            b_recv
                .iter()
                .map(|fut| {
                    let sema = sema.clone();
                    let b_send = b_send.clone();
                    rt.spawn(async move {
                        let _g = sema.acquire().await.unwrap();
                        let res = fut.await;
                        let _ = b_send.send(res);
                    })
                })
                .collect_vec()
                .into_iter()
                .for_each(|hndl| {
                    let _ = rt.block_on(hndl);
                });
        });
        Self { send, recv }
    }

    pub fn send(&self, t: impl Future<Output = T> + 'static + Send) {
        let _ = self.send.send(Box::pin(t));
    }

    pub fn recv(&self) -> AppResult<T> {
        Ok(self.recv.recv()?)
    }
}

pub trait AwaitInTokenBucket<T> {
    fn await_in_token_bucket(self, tokens: usize) -> TokenBucket<T>;
}

impl<T, Iter> AwaitInTokenBucket<T> for Iter
where
    T: Send + 'static,
    Iter: Iterator,
    Iter::Item: Future<Output = T> + Send + 'static,
{
    fn await_in_token_bucket(self, tokens: usize) -> TokenBucket<T> {
        let tb = TokenBucket::new(tokens);
        for fut in self {
            tb.send(fut);
        }
        tb
    }
}

impl<T> IntoIterator for TokenBucket<T> {
    type Item = T;
    type IntoIter = IntoIter<T>;

    fn into_iter(self) -> Self::IntoIter {
        Self::IntoIter { recv: self.recv }
    }
}

pub struct IntoIter<T> {
    recv: Receiver<T>,
}

impl<T> Iterator for IntoIter<T> {
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        self.recv.recv().ok()
    }
}
