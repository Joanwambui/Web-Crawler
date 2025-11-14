# Web Monitoring System for BooksToScrape.com
Monitors BooksToScrape.com using Scrapy + FastAPI. Detects changes, logs them in MongoDB, generates daily reports, and serves a secure REST API. Built with a production-grade folder structure, scheduler, and authentication. Basically: book-stalking, but make it techy.

Here is a professional, structured, and clean **data storytelling document** that captures your entire project, using complete sentences and formal tone, without any unnecessary emojis or casual language.

# Project Structure
<img width="447" height="611" alt="image" src="https://github.com/user-attachments/assets/23d8a638-e42f-434a-90dc-8fad77167c8f" />






#  Setup Instructions

1. Clone the repository to your machine:

   ```
   git clone <repository-url>
   cd fk_crawler
   ```

2. Create and activate a Python virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install all required dependencies:

   * Crawler and scheduler dependencies:

     ```
     pip install -r books/books/requirements.txt
     ```
   * API dependencies:

     ```
     pip install -r fastapi_app/requirements.txt
     ```

4. Create a `.env` file inside `books/books/` and `fastapi_app/`.
   These files provide the MongoDB connection string, the database name, and API authentication details.

5. Run each part of the system:

   * Start the crawler:

     ```
     cd books
     scrapy crawl book_spider
     ```
   * Start the API server:

     ```
     uvicorn fastapi_app.main:app --reload
     ```
   * Run the daily scheduler:

     ```
     python scheduler/daily_scheduler.py
     ```

---

#  Python Version and Dependency Versions

This project runs on **Python 3.11+**.

All required libraries are listed in the included requirements files:

* `books/books/requirements.txt`
* `fastapi_app/requirements.txt`

Installing these files ensures the correct versions of Scrapy, FastAPI, Motor, PyMongo, APScheduler, dotenv, and related packages are available.

---

#  `.env` File for Configuration

The `.env` file must contain the following values:

```
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/books_db
MONGODB_DB_NAME=books_db

API_KEY=supersecretapikey
RATE_LIMIT_PER_HOUR=100
```

* `MONGODB_URL` holds the full connection string for MongoDB Atlas or a local MongoDB instance.
* `MONGODB_DB_NAME` sets the name of the database used by both the crawler and the API.
* `API_KEY` controls access to the API.
* `RATE_LIMIT_PER_HOUR` defines the maximum number of requests allowed per hour for each client.





## 1. Introduction

This document outlines the design and implementation of a production-style web monitoring system developed to crawl, track, and expose book-related data from the website [BooksToScrape.com](https://books.toscrape.com). Though the target website is a sandbox e-commerce platform, the solution has been built with production-grade standards for data reliability, structure, and API access.

---

## 2. Business Context and Problem Statement
The task is to track updates on a site by building an end-to-end system that automates the following:

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

<img width="954" height="588" alt="image" src="https://github.com/user-attachments/assets/2dcea6ea-e521-412f-86a5-b01ccdcabd03" />



<img width="1394" height="262" alt="image" src="https://github.com/user-attachments/assets/c42c4f16-9f0b-4d2e-b7b1-ee797a3f0975" />



### Execution Log - Second Run with Change Detection

A second crawl detects changes and logs new or updated records in MongoDB, generating the report files. Ideally after the first crawl the rest are scheduled crawls.
Their primary goal is to check against the Mongo DB data and that provided on the website and highlight the values that appeared to have changed.

Mongo Db Original Data was 1000 as shown:
<img width="1264" height="538" alt="image" src="https://github.com/user-attachments/assets/befd5fdd-0cce-4b1d-85ee-7eec9b4bbc44" />


After the first crawl the subsequent crawls involved doing the comparison and highlighting the differences as shown:

<img width="1865" height="673" alt="image" src="https://github.com/user-attachments/assets/afc41b6f-3bda-4402-9613-8bb9eea8d761" />



---

## 5. Component 2: Scheduler and Change Detection

The project uses APScheduler to run the crawler and generate reports daily. After each run, the system compares newly scraped data against previously stored versions in MongoDB. If changes are detected, they are recorded in a dedicated collection (`books_changes`) along with the old and new values.

### Scheduler Execution Log

The following image shows a full execution cycle triggered by the scheduler. It includes running the crawler and generating reports.

The above, in order to actually identify the differences is the result after a succesful Scheduler crawl as shown below:

<img width="664" height="472" alt="image" src="https://github.com/user-attachments/assets/0a28258d-63ce-4817-b656-dd2075cccc8d" />


### MongoDB Change Log View

This is a snapshot from MongoDB showing book entries with detailed fields, crawl status, and timestamps. The database stores both new and updated entries.

<img width="1833" height="771" alt="image" src="https://github.com/user-attachments/assets/0a74c20c-5dee-40b6-a3bd-4aac949bded2" />



<img width="1864" height="749" alt="image" src="https://github.com/user-attachments/assets/674633a8-2fa4-4422-85f1-8c88aeb2d079" />


---

## 6. Component 3: RESTful API

A RESTful API was developed using FastAPI. It allows clients to:

* Retrieve books with filters such as category, price range, rating, and review count
* Sort and paginate results
* View detailed information for a specific book
* View change logs for recently updated books

Used Swagger UI as shown below to test the endpoints. You can try it yourself on this link: 


<img width="680" height="874" alt="image" src="https://github.com/user-attachments/assets/bc171dab-6beb-46bf-a4e7-f4fba97ad310" />


<img width="721" height="868" alt="image" src="https://github.com/user-attachments/assets/52020cf9-81e3-44a6-b41e-b635e1dac802" />


<img width="884" height="870" alt="image" src="https://github.com/user-attachments/assets/a2895381-cfac-4de7-8e72-09012c3f2258" />


<img width="1675" height="919" alt="image" src="https://github.com/user-attachments/assets/aec9ee53-c725-4315-8e13-94a6de13bc15" />


Every GET request if running on your machine and not yet deployed for public consumption for example on render, your terminal will return the 200 code.
This lets us know the endpoints respond well.

<img width="1840" height="152" alt="image" src="https://github.com/user-attachments/assets/716aaf9a-1f05-4690-a3ed-d95b91741bf3" />



### API Features

* API key-based authentication
* Rate limiting (100 requests per hour)
* Swagger documentation and OpenAPI schema
* Modular routing and models using Pydantic



## 7. System Flow Summary

Below is the end-to-end flow of how the system works:

1. **Scheduler** triggers the crawler daily.
2. **Crawler** scrapes the website and saves results to MongoDB.
3. **Change detection** logic compares data with previous entries and stores diffs.
4. **Reports** are generated in JSON and CSV formats.
5. **API** exposes the data securely with filtering, sorting, and documentation.

### MongoDB Final State View

All book data, including unchanged entries, is maintained with crawl timestamps and content hashes.
Remember, if changes are realize we will take snapshots of these changes then we will update our books collection with the correct changes.
<img width="1902" height="874" alt="image" src="https://github.com/user-attachments/assets/a715abd9-bf89-456d-b564-103251c1457c" />




## 8. Technology Stack

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

## 9. Evaluation Criteria and Delivery

| Requirement                            | Status    |
| -------------------------------------- | --------- |
| Scalable crawling with resume support  | Completed |
| MongoDB schema with raw HTML storage   | Completed |
| Change detection and logging           | Completed |
| Daily scheduling and report generation | Completed |
| REST API with filters and auth         | Completed |
| Documentation and test coverage        | Completed |

---

## 10. Conclusion

This project provides a complete solution for real-time monitoring of an e-commerce site. It covers data extraction, historical tracking, API access, and reporting—all built using scalable and maintainable Python practices. The architecture is modular, fault-tolerant, and fully documented, making it suitable for deployment and extension in real-world monitoring systems.

