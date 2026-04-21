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

### 4. JWT Authentication and Front-End Integration
Transitioning from simple credential verification to JWT-based authentication was a significant step. By returning a secure token and storing it in the browser's `localStorage`, we created a stateful-like experience in a stateless REST API. Implementing the front-end pages with glassmorphism design also enhanced the user experience significantly.

## Challenges Faced

### 3. Playwright E2E Testing with Docker
Setting up Playwright to run inside a Docker container locally was a challenge. It required installing specific system dependencies and browser binaries within the `Dockerfile`. However, once configured, it provided a very reliable way to test the full authentication flow from a user's perspective without environment-specific issues.

## Conclusion
The addition of JWT authentication and interactive front-end pages completes the core project requirements. The application now features a secure, modern stack with automated end-to-end testing and a robust CI/CD pipeline.
