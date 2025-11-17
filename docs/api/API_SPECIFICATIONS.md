# FoodFlow OS: API Specifications

**Document Version:** 1.0  
**Last Updated:** November 16, 2025  
**Author:** Manus AI  
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Identity Service APIs](#identity-service-apis)
5. [Tenant Service APIs](#tenant-service-apis)
6. [FoodGraph Service APIs](#foodgraph-service-apis)
7. [Forecast Service APIs](#forecast-service-apis)
8. [Vision Service APIs](#vision-service-apis)
9. [LLM Orchestration APIs](#llm-orchestration-apis)
10. [Optimization Service APIs](#optimization-service-apis)
11. [Error Handling](#error-handling)

---

## Overview

FoodFlow OS exposes RESTful APIs following OpenAPI 3.1 specifications. All APIs are versioned (e.g., `/api/v1/`) and require authentication via JWT tokens.

### Base URLs

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://api.foodflow.io
