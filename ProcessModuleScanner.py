import psutil
import argparse
import json
import xml.etree.ElementTree as ET
from html import escape
import collections.abc
import socket


def process_info(process):
    return {
        "PID": process.info['pid'],
        "Process Name": process.info['name'],
        "Command Line": process.info.get('cmdline', [])
    }

def module_scan(module_names):
    result = []
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = process.info.get('cmdline')
            if not module_names or (cmdline and any(any(module_name in arg for arg in cmdline) for module_name in module_names)):
                result.append(process_info(process))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return result

def generate_html(result):
    html_output = "<html><head><title>Module Scan</title></head><body><h1>Module Scan Results</h1>"
    html_output += "<table border='1'><tr><th>Process Name</th><th>PID</th><th>Command Line</th></tr>"

    for item in result:
        process_name = item.get('Process Name', '')
        pid = item.get('PID', '')
        cmdline = item.get('Command Line', [])

        if process_name is not None and pid is not None and cmdline is not None:
            html_output += f"<tr><td>{process_name}</td><td>{pid}</td><td>{', '.join(map(escape, cmdline))}</td></tr>"

    html_output += "</table></body></html>"
    return html_output


def generate_xml(result):
    root = ET.Element("ModuleScanResults")
    for item in result:
        process_elem = ET.SubElement(root, "Process")
        ET.SubElement(process_elem, "PID").text = str(item['PID'])
        ET.SubElement(process_elem, "ProcessName").text = item['Process Name']
        
        cmdline_value = item['Command Line']
        if cmdline_value is not None and isinstance(cmdline_value, collections.abc.Iterable):
            cmdline_text = ', '.join(map(str, cmdline_value))
        else:
            cmdline_text = str(cmdline_value)
        
        ET.SubElement(process_elem, "CommandLine").text = cmdline_text

    return ET.tostring(root, encoding='utf-8').decode('utf-8')


def main():
    parser = argparse.ArgumentParser(description="Scan Processes for Module(s)")
    parser.add_argument("-m", "--module", nargs='*', default=None, help="Specify module(s) to scan for in the running processes")
    parser.add_argument("-f", "--format", choices=['html', 'json', 'xml'], help="Specify the output format")
    args = parser.parse_args()

    result = module_scan(args.module)

    output_formats = args.format if args.format else ['html', 'json', 'xml']

    if not args.format:
        hostname = socket.gethostname()
        for format in output_formats:
            if format == 'html':
                output_content = generate_html(result)
                output_file_name = f"ModuleScan_{hostname}.html"
            elif format == 'xml':
                output_content = generate_xml(result)
                output_file_name = f"ModuleScan_{hostname}.xml"
            else:
                output_content = json.dumps(result, indent=2)
                output_file_name = f"ModuleScan_{hostname}.json"
            
            with open(output_file_name, "w") as output_file:
                output_file.write(output_content)

            print(f"Results saved to {output_file_name}")
    else:
        hostname = socket.gethostname()
        format = args.format
        if format == 'html':
            output_content = generate_html(result)
            output_file_name = f"ModuleScan_{hostname}.html"
        elif format == 'xml':
            output_content = generate_xml(result)
            output_file_name = f"ModuleScan_{hostname}.xml"
        else:
            output_content = json.dumps(result, indent=2)
            output_file_name = f"ModuleScan_{hostname}.json"

        with open(output_file_name, "w") as output_file:
            output_file.write(output_content)

        print(f"Results saved to {output_file_name}")


if __name__ == "__main__":
    main()
