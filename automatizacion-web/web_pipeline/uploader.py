import os, requests, json

# Sube archivo a API y devuelve (status_code, response_json)
def upload_file(api_url, path):
    with open(path,"rb") as f:
        r=requests.post(api_url, files={"file":(os.path.basename(path), f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}, timeout=60)
    try: data=r.json()
    except: data={"text":r.text}
    return r.status_code, data

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--file",required=True)
    a.add_argument("--api_url",default="https://desafio.somosait.com/api/upload/")
    args=a.parse_args()
    code,resp=upload_file(args.api_url,args.file)
    print(f"[UPLOAD] {args.file} -> status={code} resp={resp}")
