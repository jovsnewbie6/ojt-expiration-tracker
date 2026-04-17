# OJT Expiration Tracker

This project is a simple system designed to track OJT (On-the-Job Training) MOA (Memorandum of Agreement) expiration dates for students. It allows users to select a course and the college year of the students, and manage expiration dates effectively.

## Features

- Course selection dropdown
- College year selection dropdown
- List management for OJT MOA expiration dates
- Simple and user-friendly interface

## Project Structure

```
ojt-expiration-tracker
├── src
│   ├── app.ts                # Entry point of the application
│   ├── components
│   │   ├── courseSelector.ts  # Component for selecting courses
│   │   ├── yearSelector.ts    # Component for selecting college years
│   │   └── expirationList.ts   # Component for managing expiration dates
│   ├── models
│   │   └── student.ts         # Model for student data
│   └── types
│       └── index.ts           # Type definitions
├── package.json               # NPM configuration file
├── tsconfig.json              # TypeScript configuration file
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ojt-expiration-tracker.git
   ```
2. Navigate to the project directory:
   ```
   cd ojt-expiration-tracker
   ```
3. Install the dependencies:
   ```
   npm install
   ```

## Usage

### TypeScript version

1. Start the application:
   ```
   npm start
   ```
2. Open your browser and navigate to `http://localhost:3000` to access the application.

### Python version

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the Flask app locally:
   ```
   python app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000`.

### Production deployment

This app is ready to deploy as a standalone website.

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Start with Gunicorn:
   ```
   gunicorn app:app
   ```

#### Deploy on Render / Railway / PythonAnywhere

- Push the repo to GitHub.
- Create a new web service on Render or Railway.
- Set the start command to:
  ```
  gunicorn app:app
  ```
- Optionally use `runtime.txt` to pin Python 3.12.
- For Render, use the included `render.yaml` file so the service is configured automatically.

#### GitHub + Render

1. Install Git if needed.
2. Create a GitHub repository for this project.
3. Run `deploy.ps1` from PowerShell (or use equivalent Git commands).
4. Connect the GitHub repo in Render and select the `main` branch.
5. Render will build and deploy automatically on every push.

#### Custom domain

- Replace `your.custom.domain` in `render.yaml` with your actual domain name.
- In Render, add the same custom domain to the service settings.
- Point your domain provider DNS to Render using the records Render gives you.

#### Docker

Build and run with Docker:

```bash
docker build -t ojt-expiration-tracker .
docker run -p 5000:5000 ojt-expiration-tracker
```

Open `http://127.0.0.1:5000` once the container starts.

## Contributing

Feel free to submit issues or pull requests to improve the project. Your contributions are welcome!

## License

This project is licensed under the MIT License.