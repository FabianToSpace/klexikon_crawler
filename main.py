# main.py
import argparse
from crawler_klexikon import crawl_klexikon
from crawler_miniklexikon import crawl_miniklexikon

def main():
    parser = argparse.ArgumentParser(description="Run a crawler for Klexikon or MiniKlexikon.")
    parser.add_argument(
        "--crawler",
        choices=["klexikon", "miniklexikon"],
        required=True,
        help="Which crawler to run (klexikon or miniklexikon)."
    )
    parser.add_argument(
        "--max_pages",
        type=int,
        default=None,
        help="Optionally limit the number of category pages to crawl (e.g. 1, 2...)."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optionally specify an output JSON filename."
    )
    args = parser.parse_args()
    
    if args.crawler == "klexikon":
        df = crawl_klexikon(max_pages=args.max_pages)
        out_file = args.output or "klexikon_dataset.json"
    else:  # args.crawler == "miniklexikon"
        df = crawl_miniklexikon(max_pages=args.max_pages)
        out_file = args.output or "miniklexikon_dataset.json"
    
    # Export to JSON
    df.to_json(out_file, orient="records", force_ascii=False)
    print(f"{args.crawler.capitalize()} dataset saved to {out_file}")

if __name__ == "__main__":
    main()
