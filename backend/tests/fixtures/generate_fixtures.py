"""Script to generate Code and Structured Data test fixtures for Phase 9."""

import os
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

CODE_DIR = Path(__file__).parent / "code"
STRUCTURED_DIR = Path(__file__).parent / "structured"

CODE_DIR.mkdir(parents=True, exist_ok=True)
STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)

# 1. Python sample
(CODE_DIR / "sample_python.py").write_text("""\"\"\"Sample Python module for code intelligence testing.\"\"\"

import os
import sys
from typing import List, Optional
import requests
from pydantic import BaseModel

API_KEY = "dummy_hardcoded_secret_token_12345"

class UserAccount(BaseModel):
    \"\"\"Represents a user account in the system.\"\"\"
    user_id: int
    username: str
    is_active: bool = True

    def get_display_name(self) -> str:
        \"\"\"Return formatted display name.\"\"\"
        return f"User: {self.username}"

def fetch_user_data(user_id: int) -> Optional[UserAccount]:
    \"\"\"Fetch user data from remote service.\"\"\"
    if user_id <= 0:
        return None
    try:
        response = requests.get(f"https://api.example.com/users/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return UserAccount(**data)
    except Exception:
        pass
    return None
""", encoding="utf-8")

# 2. Python syntax error
(CODE_DIR / "sample_python_syntax_error.py").write_text("""def broken_function(
    print("Missing closing parenthesis and invalid syntax"
""", encoding="utf-8")

# 3. JavaScript sample
(CODE_DIR / "sample_javascript.js").write_text("""/**
 * Sample JavaScript module for code intelligence testing.
 */
const fs = require('fs');
const path = require('path');
const lodash = require('lodash');

class CalculationService {
    constructor(baseMultiplier = 1) {
        this.baseMultiplier = baseMultiplier;
    }

    calculateTotal(items) {
        debugger; // test diagnostic detection
        return items.reduce((sum, item) => sum + (item.price * this.baseMultiplier), 0);
    }
}

function processBatch(batchId) {
    console.log("Processing batch: " + batchId);
    return true;
}

module.exports = { CalculationService, processBatch };
""", encoding="utf-8")

# 4. TypeScript sample
(CODE_DIR / "sample_typescript.ts").write_text("""/**
 * Sample TypeScript module for code intelligence testing.
 */
import { Observable } from 'rxjs';
import axios, { AxiosResponse } from 'axios';

export interface UserProfile {
    id: string;
    email: string;
    roles: string[];
}

export type StatusType = 'active' | 'suspended' | 'pending';

export class AuthenticationManager {
    private secretKey: string = "supersecret";

    public async validateToken(token: string): Promise<boolean> {
        if (!token) {
            return false;
        }
        return token.length > 10;
    }
}

export function formatAddress(city: string, country: string): string {
    return `${city}, ${country}`;
}
""", encoding="utf-8")

# 5. React JSX sample
(CODE_DIR / "sample_react.jsx").write_text("""import React, { useState } from 'react';

export function CounterWidget({ initialCount = 0 }) {
    const [count, setCount] = useState(initialCount);

    const handleIncrement = () => {
        setCount(c => c + 1);
    };

    return (
        <div className="counter-container">
            <h3>Current Count: {count}</h3>
            <button onClick={handleIncrement}>Increment</button>
        </div>
    );
}

export default CounterWidget;
""", encoding="utf-8")

# 6. React TSX sample
(CODE_DIR / "sample_react.tsx").write_text("""import React from 'react';

export interface ButtonCardProps {
    title: string;
    count: number;
    onClick: () => void;
}

export const ButtonCard: React.FC<ButtonCardProps> = ({ title, count, onClick }) => {
    return (
        <div className="card-box">
            <h4>{title}</h4>
            <p>Score: {count}</p>
            <button onClick={onClick}>Click Me</button>
        </div>
    );
};
""", encoding="utf-8")

# 7. HTML sample
(CODE_DIR / "sample_page.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DocuMind Sample</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://cdn.example.com/lib.js"></script>
    <script>
        console.log("Inline script loaded");
    </script>
</head>
<body>
    <header id="main-header">
        <h1>Welcome to DocuMind</h1>
        <nav>
            <a href="/home">Home</a>
            <a href="/docs">Docs</a>
        </nav>
    </header>
    <main>
        <section class="content">
            <p>Intelligence platform for all files.</p>
        </section>
    </main>
</body>
</html>
""", encoding="utf-8")

# 8. CSS sample
(CODE_DIR / "sample_styles.css").write_text("""/* Main styles for DocuMind UI */
:root {
    --primary-color: #4f46e5;
    --background: #f8fafc;
}

body {
    margin: 0;
    font-family: Inter, sans-serif;
    background-color: var(--background);
}

.counter-container {
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

@media (max-width: 768px) {
    .counter-container {
        padding: 0.75rem;
    }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
""", encoding="utf-8")

# 9. Java sample
(CODE_DIR / "sample_java.java").write_text("""package com.documind.intelligence;

import java.util.List;
import java.util.ArrayList;
import java.io.Serializable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DocumentService implements Serializable {
    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);
    private final String serviceId;

    public DocumentService(String serviceId) {
        this.serviceId = serviceId;
    }

    public List<String> processDocuments(List<String> docIds) {
        log.info("Processing {} documents", docIds.size());
        List<String> results = new ArrayList<>();
        for (String id : docIds) {
            results.add("PROCESSED_" + id);
        }
        return results;
    }
}
""", encoding="utf-8")

# 10. C sample
(CODE_DIR / "sample_c.c").write_text("""#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct PacketHeader {
    int version;
    int payload_length;
};

void copy_buffer_unsafe(const char* input) {
    char dest[64];
    strcpy(dest, input); // Unsafe legacy function to trigger diagnostic
    printf("Copied buffer: %s\\n", dest);
}

int calculate_checksum(const char* data, int length) {
    int sum = 0;
    for (int i = 0; i < length; i++) {
        sum += (unsigned char)data[i];
    }
    return sum;
}
""", encoding="utf-8")

# 11. C++ sample
(CODE_DIR / "sample_cpp.cpp").write_text("""#include <iostream>
#include <string>
#include <vector>
#include <memory>

namespace documind {

class TensorNode {
public:
    TensorNode(std::string name, int dimensions) 
        : name_(std::move(name)), dimensions_(dimensions) {}

    virtual ~TensorNode() = default;

    int get_dimensions() const {
        return dimensions_;
    }

private:
    std::string name_;
    int dimensions_;
};

} // namespace documind
""", encoding="utf-8")

# 12. Go sample
(CODE_DIR / "sample_go.go").write_text("""package main

import (
	"fmt"
	"net/http"
	"github.com/gin-gonic/gin"
)

type ServerConfig struct {
	Port int
	Host string
}

func (s *ServerConfig) GetAddress() string {
	return fmt.Sprintf("%s:%d", s.Host, s.Port)
}

func StartServer(cfg ServerConfig) {
	r := gin.Default()
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "pong"})
	})
	r.Run(cfg.GetAddress())
}
""", encoding="utf-8")

# 13. Rust sample
(CODE_DIR / "sample_rust.rs").write_text("""use std::collections::HashMap;
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
""", encoding="utf-8")

# 14. PHP sample
(CODE_DIR / "sample_php.php").write_text("""<?php
namespace App\\Services;

use Psr\\Log\\LoggerInterface;
use App\\Models\\User;

class UserManager {
    private LoggerInterface $logger;

    public function __construct(LoggerInterface $logger) {
        this->logger = $logger;
    }

    public function findUserById(int $id): ?User {
        $this->logger->info("Looking up user $id");
        return null;
    }
}
""", encoding="utf-8")

# 15. SQL sample
(CODE_DIR / "sample_schema.sql").write_text("""-- Schema definition for e-commerce
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
);

SELECT u.username, o.total_amount
FROM users u
JOIN orders o ON u.user_id = o.user_id
WHERE o.status = 'completed';
""", encoding="utf-8")

# --- Structured Data Fixtures ---

# 1. Valid JSON
(STRUCTURED_DIR / "valid.json").write_text("""{
  "system": "DocuMind",
  "version": "1.0",
  "active": true,
  "settings": {
    "retries": 3,
    "timeout": 30.5
  },
  "modules": ["code", "structured", "video", "audio"]
}""", encoding="utf-8")

# 2. Nested JSON
(STRUCTURED_DIR / "nested.json").write_text("""{
  "level1": {
    "level2": {
      "level3": {
        "level4": {
          "level5": {
            "deep_key": "deep_value"
          }
        }
      }
    }
  }
}""", encoding="utf-8")

# 3. Duplicate Keys JSON
(STRUCTURED_DIR / "duplicate_keys.json").write_text("""{
  "user_id": 100,
  "role": "admin",
  "user_id": 200,
  "settings": {
    "theme": "dark",
    "theme": "light"
  }
}""", encoding="utf-8")

# 4. Invalid JSON
(STRUCTURED_DIR / "invalid.json").write_text("""{
  "name": "Broken JSON",
  "unclosed": [1, 2, 3
""", encoding="utf-8")

# 5. Valid XML
(STRUCTURED_DIR / "valid.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<catalog>
   <book id="bk101">
      <author>Gambardella, Matthew</author>
      <title>XML Developer's Guide</title>
      <genre>Computer</genre>
      <price>44.95</price>
      <publish_date>2000-10-01</publish_date>
      <description>An in-depth look at creating applications with XML.</description>
   </book>
   <book id="bk102">
      <author>Ralls, Kim</author>
      <title>Midnight Rain</title>
      <genre>Fantasy</genre>
      <price>5.95</price>
      <publish_date>2000-12-16</publish_date>
      <description>A former architect battles corporate zombies.</description>
   </book>
</catalog>
""", encoding="utf-8")

# 6. XXE Attack XML
(STRUCTURED_DIR / "xxe_attack.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE test [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<catalog>
  <data>&xxe;</data>
</catalog>
""", encoding="utf-8")

# 7. Valid YAML
(STRUCTURED_DIR / "valid.yaml").write_text("""version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    environment:
      ENV: production
  api:
    image: documind:latest
    environment:
      PORT: 8000
""", encoding="utf-8")

# 8. Alias Bomb YAML
(STRUCTURED_DIR / "alias_bomb.yaml").write_text("""a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
root: *e
""", encoding="utf-8")

# 9. Valid TOML
(STRUCTURED_DIR / "valid.toml").write_text("""[project]
name = "documind"
version = "0.9.0"
description = "Universal file intelligence platform"

[database]
host = "localhost"
port = 5432
enabled = true

[features]
code_intelligence = true
structured_data = true
""", encoding="utf-8")

# 10. Valid Parquet
schema = pa.schema([
    ("id", pa.int64()),
    ("username", pa.string()),
    ("balance", pa.float64()),
    ("is_verified", pa.bool_())
])
table = pa.Table.from_arrays([
    pa.array([1, 2, 3, 4, 5]),
    pa.array(["alice", "bob", "carol", "dan", "eve"]),
    pa.array([120.50, 450.00, 310.25, None, 99.99]),
    pa.array([True, True, False, False, True])
], schema=schema)

pq.write_table(table, str(STRUCTURED_DIR / "valid.parquet"))

# 11. Corrupted Parquet
with open(STRUCTURED_DIR / "corrupted.parquet", "wb") as f:
    f.write(b"PAR1")
    f.write(b"\x00\x01\x02\x03\x04truncated data bytes")

print("All fixtures generated successfully!")
