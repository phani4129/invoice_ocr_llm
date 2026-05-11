import os, re, glob, json, base64, logging, argparse, time
from pathlib import Path

import pandas as pd
from tabulate import tabulate
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

FIELDS = [
    "file_name",
    "Seller Name",
    "Seller Tax ID",
    "Client Name",
    "Client Tax ID",
    "Invoice Number",
    "Invoice Date",
    "Net Worth",
    "VAT",
    "Gross Worth",
    "confidence_score",
    "extraction_status",
    "notes"
]

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

PROMPT = """You are an expert invoice data extraction AI.

Extract fields from this invoice image.

RULES:
- Seller ISSUED the invoice.
- Client RECEIVED the invoice.
- Seller and Client are always different entities.
- Never mix Seller Tax ID and Client Tax ID.
- Missing fields use empty string.
- Return ONLY valid JSON.
- Do not return markdown.
- Do not add explanation.
- Invoice Date format: MM/DD/YYYY.
- Net Worth, VAT, Gross Worth: numeric only.
- confidence_score must be between 0.0 and 1.0.

Return JSON exactly like this:
{
  "Seller Name": "",
  "Seller Tax ID": "",
  "Client Name": "",
  "Client Tax ID": "",
  "Invoice Number": "",
  "Invoice Date": "",
  "Net Worth": "",
  "VAT": "",
  "Gross Worth": "",
  "confidence_score": 0.0,
  "notes": ""
}
"""


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract(client, img_path, retries=3):
    fname = Path(img_path).name

    empty = {f: "" for f in FIELDS if f != "file_name"}
    empty["confidence_score"] = 0.0
    empty["extraction_status"] = "failed"

    image_base64 = encode_image(img_path)

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_completion_tokens=1024
            )

            raw = response.choices[0].message.content.strip()

            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            data = json.loads(raw)

            for f in ["Net Worth", "VAT", "Gross Worth"]:
                data[f] = re.sub(r"[^\d.]", "", str(data.get(f, "")))

            try:
                data["confidence_score"] = round(
                    float(data.get("confidence_score", 0)), 2
                )
            except:
                data["confidence_score"] = 0.0

            data["extraction_status"] = (
                "success" if data["confidence_score"] >= 0.7 else "low_confidence"
            )

            log.info(
                "OK %-30s conf=%.2f %s",
                fname,
                data["confidence_score"],
                data["extraction_status"]
            )

            return data

        except json.JSONDecodeError as e:
            log.warning("JSON error attempt %d/%d: %s", attempt, retries, e)
            time.sleep(5)

        except Exception as e:
            err = str(e)

            if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                wait = 120 * attempt
                log.warning(
                    "Rate limit — waiting %ds attempt %d/%d",
                    wait,
                    attempt,
                    retries
                )
                time.sleep(wait)
            else:
                log.warning("Error attempt %d/%d: %s", attempt, retries, e)
                time.sleep(10)

    log.error("FAILED: %s", fname)
    empty["notes"] = "All attempts failed"
    return empty


def get_images(input_dir, start=331, end=381):
    images = []

    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        images.extend(glob.glob(os.path.join(input_dir, ext)))

    selected = []

    for img in images:
        match = re.search(r"batch1[-_](\d+)", Path(img).name, re.I)

        if match and start <= int(match.group(1)) <= end:
            selected.append(img)

    return sorted(selected)


def run(input_dir, output_csv, output_excel=None, dry_run=False):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found in .env file")

    client = Groq(api_key=api_key)

    log.info("Model: %s", MODEL)

    images = get_images(input_dir)

    if not images:
        log.error("No images found in %s. Run images.py first.", input_dir)
        return

    log.info("Found %d images to process", len(images))

    if dry_run:
        for i, img in enumerate(images, 1):
            log.info("%d. %s", i, Path(img).name)
        return

    rows = []
    start_time = time.time()

    for i, img in enumerate(images, 1):
        log.info("[%d/%d] Processing: %s", i, len(images), Path(img).name)

        result = extract(client, img)
        result["file_name"] = Path(img).name

        rows.append({f: result.get(f, "") for f in FIELDS})

        if i < len(images):
            time.sleep(10)

    df = pd.DataFrame(rows, columns=FIELDS)

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    log.info("CSV saved --> %s", output_csv)

    if output_excel:
        Path(output_excel).parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_excel, index=False)
        log.info("Excel saved --> %s", output_excel)

    total = len(df)
    success = (df["extraction_status"] == "success").sum()
    failed = (df["extraction_status"] == "failed").sum()
    elapsed = time.time() - start_time

    print("\n" + "=" * 65)
    print(f"INVOICE OCR REPORT | Model: {MODEL}")
    print("=" * 65)
    print(f"Total   : {total}")
    print(f"Success : {success}")
    print(f"Failed  : {failed}")
    print(f"Time    : {elapsed / 60:.1f} min")
    print(f"Output  : {output_csv}")
    print("=" * 65)

    cols = [
        "file_name",
        "Seller Name",
        "Client Name",
        "Invoice Number",
        "Gross Worth",
        "confidence_score",
        "extraction_status"
    ]

    print(tabulate(df[cols].head(10), headers="keys", tablefmt="grid", showindex=False))
    print(f"\nDone! Output file: {output_csv}\n")


parser = argparse.ArgumentParser()
parser.add_argument("--input-dir", "-i", default=str(Path(__file__).parent / "selected_images"))
parser.add_argument("--output-csv", "-c", default=str(Path(__file__).parent / "output" / "output.csv"))
parser.add_argument("--output-excel", "-x", default=None)
parser.add_argument("--dry-run", action="store_true")

args = parser.parse_args()

run(args.input_dir, args.output_csv, args.output_excel, args.dry_run)