import re, json

def parser_tool(text):
    text = text.split("</tool_call>")[0]
    name = re.search(r"<function=(.*?)>", text).group(1)
    params = {}
    for key, value in re.findall(r"<parameter=(.*?)>\n(.*?)\n</parameter>", text, re.DOTALL):
        params[key] = value
    try:
        params[key] = json.loads(value)
    except json.JSONDecodeError:
        params[key] = value
    return name, params