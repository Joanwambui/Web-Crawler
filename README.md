# Web Monitoring System for BooksToScrape.com
Monitors BooksToScrape.com using Scrapy + FastAPI. Detects changes, logs them in MongoDB, generates daily reports, and serves a secure REST API. Built with a production-grade folder structure, scheduler, and authentication. Basically: book-stalking, but make it techy.

Here is a professional, structured, and clean **data storytelling document** that captures your entire project, using complete sentences and formal tone, without any unnecessary emojis or casual language.

# Project Structure
<img width="447" height="611" alt="image" src="https://github.com/user-attachments/assets/23d8a638-e42f-434a-90dc-8fad77167c8f" />







## 1. Introduction

This document outlines the design and implementation of a production-style web monitoring system developed to crawl, track, and expose book-related data from the website [BooksToScrape.com](https://books.toscrape.com). Though the target website is a sandbox e-commerce platform, the solution has been built with production-grade standards for data reliability, structure, and API access.

---

## 2. Business Context and Problem Statement
Working for a content aggregation company responsible for monitoring product-related websites. The task is to track updates on a site by building an end-to-end system that automates the following:

1. Crawling and storing product data in a scalable, fault-tolerant way.
2. Detecting any changes in the data over time and maintaining historical records.
3. Serving the latest data and change logs through a secure, filterable API.

The project also demands code quality, modular organization, documentation, logging, and test coverage suitable for deployment in a production environment.

---

## 3. Project Objectives

The project is divided into three main components:

1. **Web Crawler:** Extract and persist product data using a fault-tolerant crawler.
2. **Scheduler and Change Detection:** Track changes and generate daily reports.
3. **RESTful API:** Serve the data securely with filtering and authentication.

---

## 4. Component 1: Web Crawler

The web crawler is implemented using Scrapy, and it is designed to collect structured book data including:

* Book title
* Description
* Category
* Price (including and excluding tax)
* Availability
* Number of reviews
* Rating
* Image URL
* Raw HTML
* Crawl timestamp and status

The crawler handles pagination, retry logic, transient failures, and can resume from its last successful state using Scrapy’s job directory feature.

### Execution Log - First Run

This image shows the first successful crawl. The `.env` file was correctly loaded and a connection to MongoDB was established.

![First Crawl](attachment:1.png)

### Execution Log - Second Run with Change Detection

A second crawl detects changes and logs new or updated records in MongoDB, generating the report files.

![Change Detection](attachment:2.png)

---

## 5. Component 2: Scheduler and Change Detection

The project uses APScheduler to run the crawler and generate reports daily. After each run, the system compares newly scraped data against previously stored versions in MongoDB. If changes are detected, they are recorded in a dedicated collection (`books_changes`) along with the old and new values.

### Scheduler Execution Log

The following image shows a full execution cycle triggered by the scheduler. It includes running the crawler and generating reports.

![Scheduler Execution](attachment:3.png)

### MongoDB Change Log View

This is a snapshot from MongoDB showing book entries with detailed fields, crawl status, and timestamps. The database stores both new and updated entries.

![Mongo View 1](attachment:4.png)
![Mongo View 2](attachment:5.png)

---

## 6. Component 3: RESTful API

A RESTful API was developed using FastAPI. It allows clients to:

* Retrieve books with filters such as category, price range, rating, and review count
* Sort and paginate results
* View detailed information for a specific book
* View change logs for recently updated books

### API Features

* API key-based authentication
* Rate limiting (100 requests per hour)
* Swagger documentation and OpenAPI schema
* Modular routing and models using Pydantic

### Repository Setup

A clean GitHub repository structure was used, with separation between crawler, API, scheduler, and tests.

![Repository Setup](attachment:8.png)

---

## 7. System Flow Summary

Below is the end-to-end flow of how the system works:

1. **Scheduler** triggers the crawler daily.
2. **Crawler** scrapes the website and saves results to MongoDB.
3. **Change detection** logic compares data with previous entries and stores diffs.
4. **Reports** are generated in JSON and CSV formats.
5. **API** exposes the data securely with filtering, sorting, and documentation.

### Extended Scheduler Log (Long Run)

This run includes a complete crawl and reporting cycle lasting over 22 minutes.

![Extended Scheduler Log](attachment:9.png)

### MongoDB Final State View

All book data, including unchanged entries, is maintained with crawl timestamps and content hashes.

![Final Mongo View](attachment:10.png)

---

## 8. Project Architecture and Folder Structure

```
fk_crawler/
├── books/           # Scrapy crawler code
├── fastapi_app/     # FastAPI server
├── scheduler/       # APScheduler tasks
├── reports/         # Generated report files
├── tests/           # Unit and integration tests
└── README.md
```

---

## 9. Technology Stack

| Layer         | Technology         |
| ------------- | ------------------ |
| Crawler       | Scrapy             |
| Scheduler     | APScheduler        |
| API           | FastAPI            |
| Database      | MongoDB (Atlas)    |
| ORM / Schema  | Pydantic, Motor    |
| Auth          | API Key            |
| Rate Limiting | In-memory strategy |
| Reporting     | JSON, CSV          |
| Testing       | Pytest             |
| Deployment    | GitHub             |

---

## 10. Evaluation Criteria and Delivery

| Requirement                            | Status    |
| -------------------------------------- | --------- |
| Scalable crawling with resume support  | Completed |
| MongoDB schema with raw HTML storage   | Completed |
| Change detection and logging           | Completed |
| Daily scheduling and report generation | Completed |
| REST API with filters and auth         | Completed |
| Documentation and test coverage        | Completed |

---

## 11. Conclusion

This project provides a complete solution for real-time monitoring of an e-commerce site. It covers data extraction, historical tracking, API access, and reporting—all built using scalable and maintainable Python practices. The architecture is modular, fault-tolerant, and fully documented, making it suitable for deployment and extension in real-world monitoring systems.

---

Let me know if you'd like this exported as a PDF or integrated directly into your GitHub README file.
