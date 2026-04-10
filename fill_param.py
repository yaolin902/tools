#!/usr/bin/env python3
import re, os, requests, argparse
from urllib.parse import quote

parser = argparse.ArgumentParser()
parser.add_argument("--dir", action="append", required=True)
parser.add_argument("--arg", action="append")
parser.add_argument("-m")
args = parser.parse_args()

modules = args.m.split(',') if args.m else []
valid_modules = {'sqli', 'idor'}
if set(modules).issubset(valid_modules):
    print(f'using module: {modules}')
else:
    print(f'invalid modules specified. valid modules are: {", ".join(valid_modules)}')
    exit(1)

cache = {}
path = {}

def generate_payload_sh(content, param, vuln, payloads, gen_val, file, dir):
    for [param2, (value2, _)] in gen_val.items():
        if param2 != param:
            content = re.sub(rf'\${param2}', value2, content)
            content = re.sub(rf'\$\{{{param2}\}}', value2, content)
    for i, payload in enumerate(payloads):
        content_save = re.sub(rf'\${param}', payload, content)
        content_save = re.sub(rf'\$\{{{param}\}}', payload, content_save)
        with open(f'./{dir}/{file}_{vuln}_{param}_{i}.sh', 'w') as f:
            f.write(content_save)

for dir in args.dir:
    with os.scandir(f'./{dir}') as d:
        path[dir] = [entry.name for entry in d if entry.is_file()]

for dir, files in path.items():
    for file in files:
        with open(f'./{dir}/{file}', 'r') as f:
            content = f.read()
        print(f'processing {dir}/{file}...')
        
        new_content = re.sub(r'(?s).*?(curl -X.*)', r'\1', content)
        if not re.search(r'curl -sv', new_content):
            new_content = re.sub(r'curl', 'curl -sv', new_content)
        
        if args.arg:
            for arg in args.arg:
                new_content = re.sub(r'(?m)^(curl -sv.*)$', lambda m: f'{m.group(1)}\n\t{arg} \\', new_content)
        
        new_content = re.sub(r'"(\w+)":\s*"(string|value)"', lambda m: f'"{m.group(1)}": "${m.group(1)}"', new_content)

        params = list(set(re.findall(r'\$(\w+)', new_content) + re.findall(r'\$\{(\w+)\}', new_content)))
        gen_val = {}
        
        for param in params:
            if param != "":
                if param in cache:
                    value = cache[param][0]
                    vuln = cache[param][1]
                    gen_val[param] = [value, vuln]
                    print(f'\tcache hit for {param}: {value}, {vuln}')
                else:
                    vuln = ""
                    r = requests.post('http://localhost:11434/api/generate', json={
                        'model': 'qwen2.5-coder:7b',
                        'prompt': f'Given the variable name `{param}`, generate a single fake value no spaces. Respond only the value, no quotes, nothing else.',
                        "stream": False,
                        "n": 1,
                    })
                    if modules != []:
                        vuln = {}
                        for module in modules:
                            r2 = requests.post('http://localhost:11434/api/generate', json={
                                'model': 'IHA089/drana-infinity-v1:latest',
                                'prompt': f'Is the variable name `{param}` usually targeted for `{module}`? Respond only yes or no, no explanation.',
                                "stream": False,
                                "n": 1,
                            })
                            vuln[module] = r2.json()['response'].strip()
                    
                    value = quote(r.json()['response'].strip())
                    cache[param] = [value, vuln]
                    print(f'\tgenerated value for {param}: {value}, {vuln}')
                    
                    gen_val[param] = [value, vuln]
        
        if "Get" in file:
            for [param, (value, vuln)] in gen_val.items():
                if "idor" in vuln and vuln["idor"] in ["yes", "Yes", "Yes."]:
                    generate_payload_sh(new_content, param, "idor", [str(i) for i in range(1, 6)], gen_val, file, dir)
                elif "sqli" in vuln and vuln["sqli"] in ["yes", "Yes", "Yes."]:
                    generate_payload_sh(new_content, param, "sqli", ["%27", "%22", "%23", "%3B", "%29", "%2A"], gen_val, file, dir)
        
        for [param, (value, vuln)] in gen_val.items():
            new_content = re.sub(rf'\${param}', value, new_content)
            new_content = re.sub(rf'\$\{{{param}\}}', value, new_content)
                
        with open(f'./{dir}/{file}', 'w') as f:
            f.write(new_content)
