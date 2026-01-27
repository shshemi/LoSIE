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

#[cfg(test)]
mod tests {
    use super::TokenBucket;
    use std::sync::mpsc::channel;
    use std::time::Duration;
    use std::{thread, time};

    #[test]
    fn returns_all_results() {
        let bucket = TokenBucket::new(3);

        for i in 0..6 {
            bucket.send(async move { i });
        }

        // Consuming the bucket closes the sending side and allows the background
        // thread to collect, spawn and await all handles. Collect results and
        // ensure we got all the values we sent.
        let mut results: Vec<_> = bucket.into_iter().collect();
        results.sort_unstable();
        assert_eq!(results, (0..6).collect::<Vec<_>>());
    }

    #[test]
    fn respects_concurrency_limit() {
        // Use 2 tokens and spawn 5 tasks that each report when they start and
        // then sleep for a while. We drop the bucket (via into_iter) so the
        // background thread proceeds to spawn and run the tasks.
        let bucket = TokenBucket::new(2);
        let (started_tx, started_rx) = channel();

        let total_tasks = 5usize;
        for i in 0..total_tasks {
            let started_tx = started_tx.clone();
            bucket.send(async move {
                // Signal that this task has started.
                let _ = started_tx.send(());
                // Hold the token for a bit so other tasks must wait.
                tokio::time::sleep(Duration::from_millis(200)).await;
                i
            });
        }

        // Drop our extra clone so only the tasks hold senders; when they finish
        // the started channel will also close.
        drop(started_tx);

        // Consume the bucket so the sending side is closed and background thread
        // can collect and spawn tasks.
        let iter = bucket.into_iter();

        // Give runtime a short moment to start the spawned tasks. Only up to
        // `tokens` tasks should have started within this short window.
        thread::sleep(time::Duration::from_millis(100));

        // Count how many tasks have started so far. This should be exactly the
        // number of tokens (2).
        let started_count = started_rx.try_iter().count();
        assert_eq!(
            started_count, 2,
            "expected exactly 2 tasks to have started concurrently"
        );

        // Ensure we still eventually receive all results.
        let results: Vec<_> = iter.collect();
        assert_eq!(results.len(), total_tasks);
        // Results should match 0..total_tasks (order not guaranteed)
        let mut sorted = results;
        sorted.sort_unstable();
        assert_eq!(sorted, (0..total_tasks).collect::<Vec<_>>());
    }
}
