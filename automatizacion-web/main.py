import os, argparse, json
from web_pipeline.downloader import download_all
from web_pipeline.processor import process_and_save
from web_pipeline.uploader import upload_file

def run(credentials, download_dir, outdir, headless=True, upload=False, api_url=None):
    api_url = api_url or "https://desafio.somosait.com/api/upload/"
    os.makedirs(download_dir,exist_ok=True); os.makedirs(outdir,exist_ok=True)
    items = download_all(credentials, download_dir, headless=headless)
    for name, in_path in items:
        out_path = process_and_save(name, in_path, outdir)
        print(f"[PROCESADO] -> {out_path}")
        if upload:
            code,resp = upload_file(api_url, out_path)
            print(f"[UPLOAD] {os.path.basename(out_path)} -> status={code} resp={resp}")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--credentials",default="credentials.json")
    a.add_argument("--download_dir",default="./data/raw")
    a.add_argument("--outdir",default="./data/processed")
    a.add_argument("--headless",type=lambda x:x.lower()=="true",default=True)
    a.add_argument("--upload",type=lambda x:x.lower()=="true",default=False)
    a.add_argument("--api_url",default=None)
    args=a.parse_args()
    run(args.credentials,args.download_dir,args.outdir,headless=args.headless,upload=args.upload,api_url=args.api_url)
