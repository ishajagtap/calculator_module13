# Reflection: User & Calculation API Development

## Overview
This module focused on completing the back-end logic of the FastAPI Calculator application by implementing secure user registration, login, and a full set of CRUD (BREAD) operations for calculations. The integration of these features required careful coordination between Pydantic schemas, SQLAlchemy models, and the existing `OperationFactory`.

## Key Experiences

### 1. Unified Validation with Pydantic
One of the most effective parts of the implementation was using Pydantic schemas (`CalculationCreate`, `UserLogin`, etc.) to enforce business rules before they even reached the logic layer. For example, preventing division by zero at the schema level ensures that the database is never hit with invalid state requests.

### 2. Password Security
Implementing `bcrypt` for password hashing and verification highlighted the importance of never storing plain-text credentials. By using the `verify_password` utility in the `/users/login` endpoint, we ensured that the application remains secure against common credential theft scenarios.

### 3. Factory Pattern Integration
Integrating the `OperationFactory` into the `POST /calculations` and `PUT /calculations` routes proved to be a clean way to keep the arithmetic logic decoupled from the API logic. This ensures that if new operations are added to the calculator later, the API routes don't necessarily need to be updated.

## Challenges Faced

### 1. Database Session Management in Tests
A recurring challenge was ensuring that integration tests run in isolation. Using a `Transactional session` with rollbacks after each test was crucial for maintaining a clean state in the Postgres database, especially when testing unique constraints on usernames and emails.

### 2. CI/CD Configuration
Configuring the GitHub Actions workflow to spin up a Postgres service container and wait for it to be healthy before running integration tests required precise `health-check` parameters. This ensured that the automated pipeline is robust and reliable.

## Conclusion
The completion of these features provides a solid foundational back-end for the calculator. With a functional CI/CD pipeline pushing to Docker Hub, the application is now ready for deployment and subsequent front-end integration.
