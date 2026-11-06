use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct PipelineConfig {
    pub max_workers: usize,
    pub timeout_seconds: u64,
}

pub trait Processable {
    fn process(&self) -> Result<(), String>;
}

pub fn execute_job(id: u64) -> bool {
    unsafe {
        // Trigger diagnostic for unsafe block
        let _raw_ptr: *const i32 = std::ptr::null();
    }
    id > 0
}
