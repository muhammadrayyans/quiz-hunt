# Quiz Hunt

Quiz Hunt is a Python automation project that opens a Google Form in Chrome, reads the visible multiple-choice questions, and uses Gemini to choose the most likely correct answer automatically.

It is designed for educational or personal use on forms you own or have permission to automate.

## Project overview

This project combines:

- Playwright for browser automation
- Chrome remote debugging to connect to an already running browser
- Google Gemini for answer selection
- A lightweight flow that reads each question, asks Gemini for the best option, selects it, and advances through the form until submission

## Requirements

Before running the project, make sure you have:

- Python 3.10 or newer
- Google Chrome installed
- A valid Gemini API key
- Access to the Google Form you want to complete

## Setup

### 1. Clone or open the project

```bash
cd "E:\C drive -E\Collage\programing\quiz-hunt"
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root and add:

```env
GEMINI_API_KEY=your_api_key_here
```

You can also use `GOOGLE_API_KEY` instead if that is how your environment is configured.

Optional settings:

```env
GEMINI_MODEL=gemini-3.5-flash
QUIZ_REQUEST_INTERVAL_SECONDS=2.5
```

## Launch Chrome with remote debugging enabled

The project expects Chrome to be running with remote debugging enabled on port `9222`.

A helper script is included:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
./chrome.sh
```

This script launches Chrome using a custom profile directory and the remote debugging port.

If you prefer to launch Chrome manually, use a command similar to:

```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="E:\C drive -E\Collage\programing\quiz-hunt\.chrome-profile"
```

## Usage

### 1. Open the Google Form in Chrome

Open the quiz or form in the Chrome window that is connected to port `9222`.

### 2. Run the automation

From the project root:

```bash
python .\src\main.py
```

Or with custom timing:

```bash
python .\src\main.py --request-interval 3.0
```

You can also override the Chrome debugging endpoint:

```bash
python .\src\main.py --cdp-url http://127.0.0.1:9222
```

## Command-line options

```bash
python .\src\main.py --help
```

Available options include:

- `--cdp-url`: Chrome DevTools Protocol URL
- `--request-interval` / `--request-delay`: delay between Gemini requests

## How it works

1. The script connects to Chrome through the CDP endpoint.
2. It locates a Google Form page in the browser.
3. It reads the visible question blocks and answer options.
4. It sends each question to Gemini with the option list.
5. Gemini returns the correct zero-based option index.
6. The project selects that answer and advances to the next page.
7. When no next page is available, it submits the form.

## Important notes

- This script is intended for Google Forms that you own or are authorized to complete.
- The browser profile directory is stored under `.chrome-profile` and is separate from the default Chrome profile.
- If Chrome is not running with remote debugging enabled, the app will fail to connect.
- If Gemini returns an invalid answer or the form structure changes, the script will raise an error instead of silently continuing.

## Troubleshooting

### Chrome is not connecting

Check that Chrome is running with:

- `--remote-debugging-port=9222`
- a valid user-data directory

### Gemini key error

Make sure the `.env` file exists and contains a valid `GEMINI_API_KEY` or `GOOGLE_API_KEY` value.

### No Google Form page found

Open a Google Form in the browser before running the script, or make sure the browser is the one launched with CDP enabled.

## License

This project is provided as-is for local educational use.
