# Web Scraper

This is a web scraping application built with Flask (Python) for the backend and HTML/CSS/JavaScript for the frontend. It allows users to input a URL, scrape article titles, URLs, and dates from the page, and display them in a list. Users can delete items from the list and export the data in CSV or JSON format.

## Features

- **Scrape Articles:** Extract article titles, URLs, and publication dates from a given website.
- **List Management:** View, delete, and manage the extracted data.
- **Export Data:** Export the data in CSV or JSON format.
- **Caching:** Cache scraped data for 5 minutes to reduce redundant requests.
- **Rate Limiting:** Prevent abuse with rate limiting (10 requests per minute).

## Technologies Used

- **Backend:** Flask, BeautifulSoup, Requests, Flask-Caching, Flask-Limiter
- **Frontend:** HTML, CSS, JavaScript, Tailwind CSS
- **Other Tools:** Validators, Regex, CSV, JSON, StringIO, BytesIO

## How to Run the Application

### Prerequisites
- Python 3.x
- Flask (`pip install flask`)
- BeautifulSoup (`pip install beautifulsoup4`)
- Requests (`pip install requests`)

## Installation

1. **Clone the repository**:
   
   ```bash
   git clone https://github.com/AugustineTamba/web-scraper.git
   cd web-scraper

2. **Install dependencies**:

  ```bash
  pip install -r requirements.txt
  ```

3. Run the application:

  ```bash
  python app.py
  ```

4. Open your browser and navigate to http://127.0.0.1:5000.

### Usage

- Enter a URL in the input field and click "Scrape" to extract article data.
- View the extracted data in the table below.
- Use the "Delete" button to remove items from the list.
- Export the data by clicking "Export as CSV" or "Export as JSON".

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the [LICENSE](https://chat.deepseek.com/a/chat/s/LICENSE) file for details.

### SCREENSHOTS

<img src="https://github.com/user-attachments/assets/b98ef9ad-0f0e-4998-9e0e-9100000b6ae0" width="300">
<img src="https://github.com/user-attachments/assets/115f5822-7bd2-4635-b3bc-995abd65d8a4" width="300">
<img src="https://github.com/user-attachments/assets/c1001446-29f6-4ba6-8379-8b9af3f7abfc" width="300">
<img src="https://github.com/user-attachments/assets/15a138c7-142a-4f1b-baf4-b00152e667ee" width="300">
