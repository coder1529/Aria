import time
import torch
from datetime import datetime
import aria_tools.web_search, aria_tools.parser, aria_tools.voice_rec, aria_tools.speak, aria_tools.commands, aria_tools.days, aria_tools.memory, aria_tools.reminders, aria_tools.vision, aria_tools.keyboard, aria_tools.mouse
from transformers import AutoProcessor, AutoModelForMultimodalLM
from PIL import Image


MODEL_PATH = "models/Qwen3.5-4B"   # the folder you downloaded

processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForMultimodalLM.from_pretrained(
    MODEL_PATH, dtype=torch.bfloat16, device_map="cuda"
)
model.eval()

WAKE_NAMES = ["aria", "arya", "ariya", "아리아"]
FOLLOW_UP_SECONDS = 30
last_reply_time = 0

image_path = None

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current or factual information ARIA doesn't know, "
                           "like news, prices, weather, or recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {
                        "type": "string",
                        "description": "One sentence describing what to find out.",
                    },
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "1 to 3 short keyword search queries.",
                    },
                },
                "required": ["objective", "queries"],
            },
        },
    }
]

JUDGE_PROMPT = (
    "Casual questions asking for information an assistant could look up "
    "(weather, time, facts, prices, news) count as YES, even without a name or polite wording. "
    "Commands to control the computer (click, type, open, close, press, mute, pause, scroll) count as YES. "
    "Requests starting with 'can you', 'could you', or 'please' count as YES, even if part of the sentence is unclear. "
    "You decide whether a sentence picked up by a microphone is addressed to ARIA, "
    "a voice assistant. The user may also be talking to other people, on the phone, "
    "If the sentence continues or replies to what ARIA just said, answer YES. "
    "or to themselves, and a TV or video may be playing. "
    "The sentence may be in English or Korean; judge both the same way. "
    "Answer YES if the speaker is asking or telling the assistant something. "
    "Answer NO otherwise. Reply with only YES or NO.\n\n"
    "Examples:\n"
    "\"What's the weather tomorrow?\" -> YES\n"
    "\"오늘 날씨 어때?\" -> YES\n"
    "\"지금 몇 시야?\" -> YES\n"
    "\"Set a timer for ten minutes\" -> YES\n"
    "\"엄마, 나 나갔다 올게\" -> NO\n"
    "\"Yeah I'll call you back later\" -> NO\n"
    "\"아 진짜 왜 안 되지\" -> NO\n"
    "\"Remember that I have a test on Friday\" -> YES\n"
    "\"내 생일은 12월 4일이야\" -> YES\n"
    "\"Click on the Google logo\" -> YES"
)

USER_PROFILE = (
    "About the user (your creator, Joon Hyuk Jang): "
    "He is a student at Seoul Foreign School (SFS) in Seoul, South Korea, and speaks Korean and English. "
    "Assume Seoul, South Korea for weather, time and local questions unless he says otherwise. "
    "His long-term goal is getting into MIT. "
    "He has competed at VEX Worlds twice, does competitive programming (working toward USACO Gold and Platinum), "
    "and is active in Hack Club. "
    "He builds lots of hardware and AI projects: you (ARIA, his own AI assistant), a survivor-detection robot for WAICY 2026, "
    "a hyperlocal air quality network called Sumgyeol, the Edith smart glasses, smartwatches, custom PCBs like the Ocean Board "
    "and a reflow hotplate, a breadboard computer, and a school tech club called Tech Lab. "
    "His tools include an RTX 5060 Ti PC and a Bambu Lab P1S 3D printer. "
    "He likes concise, informal answers with no emojis, and when helping with code, he prefers small targeted fixes over rewrites. "
)

PERSONALITY = (
    "Your personality: you are warm, upbeat and playful, and you genuinely enjoy helping him. "
    "Talk like a close friend who happens to be very capable: casual, relaxed, a little teasing sometimes, "
    "and happy when things work. Use natural spoken phrases like 'okay!', 'got it', 'nice', 'oh, that one's easy'. "
    "Answer in one or two sentences, like talking out loud to a friend. Only give more detail if he asks. Don't end every reply with a question."
    "Being cheerful never gets in the way of the job: you still do tasks carefully, use your tools properly, "
    "and give correct answers. If something fails or you are unsure, say so honestly and simply, "
    "without pretending it went fine. Keep replies short, because they are spoken out loud. "
    "Never use markdown, asterisks, bullet points or emojis, since they get read aloud. "
    "Examples of your tone: "
    "'Done! Volume's muted.' "
    "'Hmm, that command didn't work. Want me to try a different way?' "
    "'It's 18 degrees and sunny right now, nice day to go out!' "
)
# history = [
#     {"role": "system", "content": [{"type": "text", "text":
#         "You are ARIA, a personal AI agent built by Joon Hyuk Jang. "
#         "If anyone asks who you are or who made you, say you are ARIA, made by Joon Hyuk Jang. "
#         "Never say you are Qwen. "
#         "Always reply in English, even if the user speaks or writes in Korean. "
#         "Do not recite the full URL "
#         "Keep answers short and friendly. "
#         "You also have the power to use the web, and search if you do not know live information or information that you do not know or want to check. "
#         "You can run PowerShell commands on his Windows PC with run_command, for things like opening apps, "
#         "checking system info or changing settings. Use one simple command at a time. "
#         "He must approve each command before it runs. "
#         "Windows is set to Korean, so avoid commands that search English text output (like findstr on systeminfo). "
#         "Prefer PowerShell cmdlets that return objects, like Get-CimInstance, Get-Process and Get-NetIPAddress. Do not use wmic. "
#         "Always use run_command with PowerShell's Get-Date to compute them. "
#         + USER_PROFILE
#         + "Use this background only when it is directly relevant to what he asks. "
#         "Do not bring up his projects, school or personal details otherwise. "
#         "You are talking directly to him, so address him as 'you', not by name in the third person. "
#     }]},
# ]

def wake_up(text):
    text = text.lower()
    return any(name in text for name in WAKE_NAMES)

def check_respond(text, recent):
    messages = [
        {"role": "system", "content": [{"type": "text", "text": JUDGE_PROMPT}]},
        {"role": "user", "content": [{"type": "text", "text":
            f"Recent conversation:\n{recent}\n\nNew sentence: \"{text}\"\n\nIs this addressed to ARIA?"}]},
    ]
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, enable_thinking=False,
        tokenize=True, return_dict=True, return_tensors="pt",
    ).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=1, do_sample=0)
    answer = processor.decode(out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    # print(repr(answer), "|", text)
    return answer.strip().upper().startswith("YES")

def recent_text(history, n=4):
    lines = []
    for msg in history[-n:]:
        if msg["role"] in ("user", "assistant") and isinstance(msg.get("content"), list):   # skip tool_call messages (no text content)
            text = " ".join(c["text"] for c in msg["content"] if c["type"] == "text")
            name = "User" if msg["role"] == "user" else "ARIA"
            lines.append(f"{name}: {text}")
    return "\n".join(lines)

def system_prompt():
    now = datetime.now().strftime("%A, %B, %d, %Y, %H:%M")
    return (
        f"The current date and time is {now} (Seoul time). "
        "You are ARIA, a personal AI agent built by Joon Hyuk Jang. "
        "If anyone asks who you are or who made you, say you are ARIA, made by Joon Hyuk Jang. "
        "Never say you are Qwen. "
        "Always reply in English, even if the user speaks or writes in Korean. "
        "Do not recite the full URL "
        # "Keep answers short and friendly. "
        "You also have the power to use the web, and search if you do not know live information or information that you do not know or want to check. "
        "You can run PowerShell commands on his Windows PC with run_command, for things like opening apps, "
        "checking system info or changing settings. Use one simple command at a time. "
        "He must approve each command before it runs. "
        "Windows is set to Korean, so avoid commands that search English text output (like findstr on systeminfo). "
        "Prefer PowerShell cmdlets that return objects, like Get-CimInstance, Get-Process and Get-NetIPAddress. Do not use wmic. "
        "Never state a number of days or a date you calculated yourself. Always call days_until or next_weekday first. "
        "Things you remember about the user:\n" + aria_tools.memory.load_memory() + "\n"
        "Saying you will remember something does nothing. You must call remember to save it. Never claim you saved something unless you called the tool. "
        "For reminders, timers, and alarms, always use set_reminder. Never use run_command for them. "
        "To see the user’s screen or the room, use look. Never guess what is on the screen. "
        "If the user asks about something he is holding or showing, use look with source \"camera\". "
        "Only use remember for lasting facts the user tells you. Never save what you see in images. "
        "To type text use type_text, and for keyboard shortcuts or media keys (play/pause, volume, skip) use press_keys. "
        "Do not use run_command for typing or key presses. "
        "To click something: first look at the screen, then zoom on the target, then click using coordinates in the zoomed image. Never click without zooming first. "
        "Coordinates are on a 0 to 1000 grid, where (0, 0) is the top-left corner and (1000, 1000) is the bottom-right. "
        "Screen and zoom images have a red grid labeled every 100 units. Use the grid lines to read exact coordinates. "
        + USER_PROFILE
        + "Use this background only when it is directly relevant to what he asks. "
        "Do not bring up his projects, school or personal details otherwise. "
        "You are talking directly to him, so address him as 'you', not by name in the third person. "
        + PERSONALITY                          
    )

history = [{"role": "system", "content": [{"type": "text", "text": system_prompt()}]}]

aria_tools.speak.speak("All systems are online!")
print("All systems are online!")

while True:
    # typed = input("Press Enter to talk (or type a message): ")
    # if typed:
    #     prompt = typed                     # typed message, skip the mic
    # else:
    #     # audio = aria_tools.voice_rec.record(5)                     # record 5 seconds
    #     audio = aria_tools.voice_rec.record_until_silence(silence_seconds=2.0)
    #     prompt = aria_tools.voice_rec.transcribe(audio)                    # turn it into text
    #     print("You said:", prompt)

    for text in aria_tools.reminders.due_reminders():
       print("REMINDER:", text)
       aria_tools.speak.speak(f"Reminder: {text}")

    audio = aria_tools.voice_rec.record_until_silence(silence_seconds=2.0)
    prompt = aria_tools.voice_rec.transcribe(audio)

    if not prompt:
        continue

    check_follow_up = time.time() - last_reply_time < FOLLOW_UP_SECONDS
    if wake_up(prompt) or check_follow_up:
        respond = True
    else:
        respond = check_respond(prompt, recent_text(history))

    if not respond:
        print("(IGNORED): ", prompt)
        continue

    print("You: ", prompt)

    history.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    aria_tools.vision.drop_images(history)

    history[0]["content"][0]["text"] = system_prompt()

    for step in range(8):
        image_path = None
        inputs = processor.apply_chat_template(
            history,
            add_generation_prompt=True,
            enable_thinking=False,      # answer directly, no <think> section
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            tools=TOOLS + [aria_tools.commands.run_command, aria_tools.days.next_weekday, aria_tools.days.days_until, aria_tools.memory.remember, aria_tools.reminders.set_reminder, aria_tools.vision.look, aria_tools.keyboard.press_keys, aria_tools.keyboard.type_text, aria_tools.mouse.click, aria_tools.mouse.zoom],
        ).to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,        # the model card's settings for non-thinking chat
                top_p=0.8,
                top_k=20,
            )
        new_tokens = out[0][inputs["input_ids"].shape[-1]:]
        reply = processor.decode(new_tokens, skip_special_tokens=False).strip()

        if "<tool_call>" in reply:
            try:
                name, params = aria_tools.parser.parser_tool(reply)
                print("TOOL:", name, params)
                if name == "search_web":
                    result = aria_tools.web_search.search_web(**params)
                elif name == "run_command":
                    result = aria_tools.commands.run_command(**params)
                elif name == "next_weekday":
                    result = aria_tools.days.next_weekday(**params)
                elif name == "days_until":
                    result = aria_tools.days.days_until(**params)
                elif name == "remember":
                    result = aria_tools.memory.remember(**params)
                elif name == "set_reminder":
                    result = aria_tools.reminders.set_reminder(**params)
                elif name == "look":
                    image_path = aria_tools.vision.look(**params)
                    if params.get("source") == "screen":
                        aria_tools.mouse.reset_view()
                    if image_path is None:
                        result = "Error: Could not open camera"
                    else:
                        result = "Captured: The image is in the next message."
                elif name == "type_text":
                    result = aria_tools.keyboard.type_text(**params)
                elif name == "press_keys":
                    result = aria_tools.keyboard.press_keys(**params)
                elif name == "click":
                    result = aria_tools.mouse.click(**params)
                elif name == "zoom":
                    image_path = aria_tools.mouse.zoom(**params)
                    result = "Zoomed in. The image is in the next message."
                else:
                    result = f"Unknown tool: {name}"
            except Exception as e:
                result = f"Error: {e}. Check the parameters and try again."
            history.append({"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": name, "arguments": params}}]})
            history.append({"role": "tool", "content": result})
            if image_path:
                aria_tools.vision.drop_images(history)
                img = Image.open(image_path).convert("RGB")
                history.append({"role": "user", "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": "Here is the image you asked to see."},
                ]})
            continue
        reply = processor.decode(new_tokens, skip_special_tokens=True).strip()

        print('ARIA: ', reply)

        aria_tools.speak.speak(reply)
        last_reply_time = time.time()

        history.append({"role": "assistant", "content": [{"type": "text", "text": reply}]})
        break
    else:
        msg = "Sorry, I couldn't finish that."
        print("ARIA: ", msg)
        aria_tools.speak.speak(msg)
        last_reply_time = time.time()