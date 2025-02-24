# Klexikon & MiniKlexikon Dataset Crawler

This repository contains Python scripts for crawling datasets from [Klexikon](https://klexikon.zum.de/) and [MiniKlexikon](https://miniklexikon.zum.de/). The crawlers extract article content, clean it (by removing unwanted sections), split it into paragraphs and sentences, and then export the results as a structured JSON dataset.

## Project Structure

~~~plaintext
.
├── crawler.py                  # Shared logic for crawling and parsing articles
├── crawler_klexikon.py         # Site-specific crawler for Klexikon
├── crawler_miniklexikon.py     # Site-specific crawler for MiniKlexikon
├── main.py                     # Entry point to run a selected crawler via command-line
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .gitignore                  # Git ignore file (JSON exports are ignored)
~~~

## Features

- **Modular Design:**  
  Shared logic is maintained in `crawler.py` while site-specific crawling rules are defined in `crawler_klexikon.py` and `crawler_miniklexikon.py`.

- **Pagination Support:**  
  The crawlers automatically follow "nächste Seite" links to gather all article URLs.

- **Custom Content Cleaning:**  
  Unwanted sections such as `<div class="klexibox">` are removed.  
  - **Klexikon:** Truncated at `<div class="mw-inputbox-centered">`.
  - **MiniKlexikon:** Truncated at the first `<hr>` tag.

- **Content Extraction:**  
  Articles are split into paragraphs (keeping inline tags intact) and further divided into sentences.

- **Progress Tracking:**  
  Uses `tqdm` to display a progress bar during the crawling process.

- **JSON Export:**  
  The final dataset is exported as a JSON file with the following structure:

~~~json
[
  {
    "ID": 1,
    "WikiLink": "https://klexikon.zum.de/wiki/Example",
    "Paragraphs": [
      "Paragraph 1 text...",
      "Paragraph 2 text..."
    ],
    "Sentences": [
      "Sentence 1",
      "Sentence 2",
      "..."
    ]
  },
  ...
]
~~~

## Installation

1. **Clone the Repository:**

   ~~~bash
   git clone https://github.com/FabianToSpace/klexikon_crawler.git
   cd klexikon_crawler
   ~~~

2. **Set Up a Virtual Environment (Optional):**

   ~~~bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ~~~

3. **Install Dependencies:**

   ~~~bash
   pip install -r requirements.txt
   ~~~

## Usage

The main entry point is `main.py`, which allows you to choose the crawler via command-line arguments.

### Running the Klexikon Crawler

~~~bash
python main.py --crawler klexikon
~~~

This command crawls Klexikon and saves the output to `klexikon_dataset.json` by default.

### Running the MiniKlexikon Crawler

~~~bash
python main.py --crawler miniklexikon
~~~

This command crawls MiniKlexikon and saves the output to `miniklexikon_dataset.json` by default.

### Additional Options

- **Limit the Number of Pages:**

   ~~~bash
   python main.py --crawler klexikon --max_pages 2
   ~~~

- **Specify a Custom Output File:**

   ~~~bash
   python main.py --crawler miniklexikon --output custom_output.json
   ~~~

## Contributing

Contributions are welcome! Please fork this repository and open a pull request with your improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
