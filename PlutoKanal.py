from pyrogram import Client, filters, idle
import sqlite3
import asyncio
import random
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums.chat_type import ChatType
from threading import Timer

API_ID = Api id gir
API_HASH = "Api hash gir"
BOT_TOKEN = "Token gir"
session_name = "PlutoKanal"



bot = Client(session_name, api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)




# Veritabanını başlatın
conn = sqlite3.connect('kingdoms_game.db', check_same_thread=False)
cursor = conn.cursor()


# `members` tablosuna `kingdom_id` sütununu ekleyin
try:
    cursor.execute("ALTER TABLE members ADD COLUMN kingdom_id INTEGER")
except sqlite3.OperationalError:
    pass  # Kolon zaten mevcut olabilir


# Gerekli tabloları oluşturun
cursor.execute('''CREATE TABLE IF NOT EXISTS kingdoms (
                    group_id INTEGER PRIMARY KEY,
                    owner_id INTEGER,
                    name TEXT,
                    gold INTEGER DEFAULT 0,
                    barracks INTEGER DEFAULT 1,
                    castle INTEGER DEFAULT 1,
                    army INTEGER DEFAULT 100
                    )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS members (
                    user_id INTEGER PRIMARY KEY,
                    group_id INTEGER,
                    role TEXT,
                    gold INTEGER DEFAULT 0,
                    debt INTEGER DEFAULT 0,
                    FOREIGN KEY(group_id) REFERENCES kingdoms(group_id)
                    )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS bets (
                    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    number INTEGER,
                    amount INTEGER,
                    FOREIGN KEY(user_id) REFERENCES members(user_id),
                    FOREIGN KEY(group_id) REFERENCES kingdoms(group_id)
                    )''')

conn.commit()

NAME = "yetimhanekumarbazibot"
OWNER_ID = 2063166406

moon = [
    [
        InlineKeyboardButton(text="📚 Komutlar", callback_data="yardim"),
    ],
    [
        InlineKeyboardButton(
            text="Gruba Ekle",
            url=f"https://t.me/{NAME}?startgroup=s&admin=delete_messages",
        ),
    ],
    [
        InlineKeyboardButton(text="👤 Owner", user_id=OWNER_ID),
        InlineKeyboardButton(text="📢 Kanal", url=f"https://t.me/plutokanal"),
    ],
]


pluto = [
    [
        InlineKeyboardButton(text="⬅️ Geri", callback_data="geri"),
    ],
]




plutokanal = [
    [
        InlineKeyboardButton(text="🗑 Sil", callback_data="kapat"),
    ],
]


YARDIM = f"""
/olustur - Krallık oluşturur.
/kralligim - Krallığın ile bilgi verir.
/yukselt - Ordunu, kaleni ve kışlanı seviyesini yükseltir.
/savas - Hedef krallığa savaş açar.
/analiz - Krallıkları analiz eder.
/slot - Aşkta kaybeden kumarda kazanır.
/rulet - Rulet oyunu açar.
/bakiyem - Kendi bakiyeni gösterir.
"""

async def is_admin(user_id, group_id):
    kapital = await bot.get_chat_member(group_id, user_id)
    if kapital.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return False
    return True


user_bets = {}

# Bahis komutu
@bot.on_message(filters.command("rulet"))
async def rulet_oyunu(client: Client, message: Message):
    group_id = message.chat.id

    await client.send_animation(group_id, 
                                animation=f"https://graph.org/file/fbff942a404c54b6565b9.gif",
                                caption = f"Rulet oyunu başladı! Bahislerinizi 60 saniye içinde yapın. /bahis [numara] [miktar] komutunu kullanarak bahis yapabilirsiniz."
                                )
    await asyncio.sleep(60)
    await finish_game(client, group_id)

# Bahis komutu
@bot.on_message(filters.command("bahis"))
async def bahis_yap(client: Client, message: Message):
    args = message.text.split()
    if len(args) != 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply_text("Geçersiz komut. Lütfen örneğin /bahis 5 100 şeklinde bir numara ve miktar belirtin.")
        return
    
    numara = int(args[1])
    miktar = int(args[2])
    group_id = message.chat.id
    user_id = message.from_user.id

    if numara < 0 or numara > 36:
        await message.reply_text("Numara 0 ile 36 arasında olmalıdır.")
        return
    
    if miktar <= 0:
        await message.reply_text("Bahis miktarı 0'dan büyük olmalıdır.")
        return

    # Kullanıcının yeterli altını olup olmadığını kontrol et
    cursor.execute("SELECT gold FROM members WHERE user_id = ? AND group_id = ?", (user_id, group_id))
    user_gold = cursor.fetchone()
    if not user_gold or user_gold[0] < miktar:
        await message.reply_text("Yetersiz altın.")
        return

    # Aynı numaraya bahis yapmayı engelle
    cursor.execute("SELECT * FROM bets WHERE group_id = ? AND number = ?", (group_id, numara))
    existing_bet = cursor.fetchone()
    if existing_bet:
        await message.reply_text("Bu numara zaten bahis yapıldı, başka bir numara seçin.")
        return

    # Bahisi kaydet
    cursor.execute("INSERT INTO bets (user_id, group_id, number, amount) VALUES (?, ?, ?, ?)",
                   (user_id, group_id, numara, miktar))
    conn.commit()

    # Bahis miktarını kullanıcının hazinesinden düş
    cursor.execute("UPDATE members SET gold = gold - ? WHERE user_id = ? AND group_id = ?", 
                   (miktar, user_id, group_id))
    conn.commit()

    await message.reply_text(f"Bahisiniz alındı! {numara} numarasını ve {miktar} altın miktarını belirttiniz.")

# Oyun bitirme ve kazananı açıklama fonksiyonu
async def finish_game(client: Client, chat_id: int):
    cursor.execute("SELECT user_id, number, amount FROM bets WHERE group_id=?", (chat_id,))
    bets = cursor.fetchall()
    
    if not bets:
        await client.send_message(chat_id, "Oynayan hiç kimse yok.")
        return

    kazanan_numara = random.randint(0, 36)
    kazananlar = [user_id for user_id, numara, amount in bets if numara == kazanan_numara]
    kazanan_mesajı = f"Oyun bitti! Kazanan numara: {kazanan_numara}.\n"
    if kazananlar:
        toplam_bahis = sum(amount for _, _, amount in bets)
        vergi = toplam_bahis * 0.25
        ödül = toplam_bahis - vergi
        kazanan_mesajı += "Kazananlar:\n"
        for user_id in kazananlar:
            user = await client.get_users(user_id)
            cursor.execute("UPDATE members SET gold = gold + ? WHERE user_id = ? AND group_id = ?", 
                           (ödül / len(kazananlar), user_id, chat_id))  # Ödül paylaşımı
            kazanan_mesajı += f"{user.mention} - Ödül: {ödül / len(kazananlar)} altın\n"
            
            # Vergi ödendiğine dair mesaj
            await client.send_message(chat_id, f"{user.mention} krallığa {vergi / len(kazananlar)} altın vergi ödedi.")

        # Vergiyi krallığa ekle
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id = ?", 
                       (vergi, chat_id))
        conn.commit()
    else:
        kazanan_mesajı += f"Kumarda kaybeden aşkata kazanır ❤️‍🔥\nBu elde kazanan yok tüm bahisler krallığa aktarıldı. 👑"
        toplam_bahis = sum(amount for _, _, amount in bets)
        
        # Tüm bahisleri krallığın hazinesine ekle
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id = ?", 
                       (toplam_bahis, chat_id))
        conn.commit()

    # Bahisleri temizle
    cursor.execute("DELETE FROM bets WHERE group_id=?", (chat_id,))
    conn.commit()
    
    await client.send_message(chat_id, kazanan_mesajı)


@bot.on_message(filters.command('start'))
async def start(client, message):
    chat_id = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        await client.send_message(
            chat_id,
            text=f"๏ Merhaba {message.from_user.mention} Grubunun arası etkileşimi için yapılmış oyun botuyum.\n๏ Komutlar hakkında bilgi almak için komutlar buttonuna basınız.",
            reply_markup=InlineKeyboardMarkup(moon),
        )


@bot.on_callback_query()
async def cb_handler(_, query: CallbackQuery):
    if query.data == "yardim":
        await query.message.edit_text(
            text=YARDIM,
            reply_markup=InlineKeyboardMarkup(pluto),
            disable_web_page_preview=True,
        )
    elif query.data == "kapat":
        await query.message.delete()
        await query.answer("Menü Kapandı!", show_alert=True)
    elif query.data == "geri":
        await query.message.edit(
            text=f"๏ Merhaba  {query.from_user.mention} Grubunun arası etkileşimi için yapılmış oyun botuyum.\n๏ Komutlar hakkında bilgi almak için komutlar buttonuna basınız.",
            reply_markup=InlineKeyboardMarkup(moon),
        )


@bot.on_message(filters.command('olustur'))
async def create_kingdom(client, message):
    group_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(user_id, group_id):
        await message.reply("Bu komutu kullanma yetkiniz yok.")
        return

    # Krallık zaten var mı kontrol et
    cursor.execute("SELECT * FROM kingdoms WHERE group_id=?", (group_id,))
    existing_kingdom = cursor.fetchone()
    if existing_kingdom:
        await message.reply("Bu grup için zaten bir krallık oluşturulmuş.")
        return

    # Krallık ismini belirle
    group_name = message.chat.title

    # Krallığı oluşturun
    cursor.execute("INSERT INTO kingdoms (group_id, owner_id, name) VALUES (?, ?, ?)", (group_id, user_id, group_name))
    conn.commit()

    # Gruptaki her üye için altın ekle
    total_gold = 0
    async for member in client.get_chat_members(group_id):
        total_gold += 25000  # Krallığa katkı
        cursor.execute("INSERT OR IGNORE INTO members (user_id, group_id, role, gold) VALUES (?, ?, ?, ?)", 
                       (member.user.id, group_id, 'halk', 12000))  # Üyeye kendi hazinesinde 12.000 altın
    cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id=?", (total_gold, group_id))
    conn.commit()

    # Grup sahibi yöneticidir
    cursor.execute("UPDATE members SET role = ? WHERE user_id = ? AND group_id = ?", ('yönetici', user_id, group_id))
    conn.commit()

    await message.reply(f"👑 Krallığınız '{group_name}' başarıyla oluşturuldu ve her üye için 25.000 🪙 altın krallığa, 12.000 🪙 altın kendi hazinesine eklendi!")
    
@bot.on_message(filters.command('kralligim'))
async def show_kingdom(client, message):
    group_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(user_id, group_id):
        await message.reply("Bu komutu kullanma yetkiniz yok.")
        return

    cursor.execute("SELECT * FROM kingdoms WHERE group_id=?", (group_id,))
    kingdom = cursor.fetchone()
    if kingdom:
        reply = (
            f"Krallık Adı: {kingdom[2]}\n"
            f"Altın: {kingdom[3]}\n"
            f"Kışla: {kingdom[4]}\n"
            f"Kale: {kingdom[5]}\n"
            f"Ordu: {kingdom[6]}"
        )
        await message.reply(reply)
    else:
        await message.reply("Önce krallığınızı oluşturmalısınız.")

@bot.on_message(filters.command('yukselt'))
async def upgrade_kingdom(client, message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Kullanım: /yukselt [kışla|kale|ordu]")
        return

    upgrade_type = args[1]
    group_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(user_id, group_id):
        await message.reply("Yalnızca yöneticiler yükseltme yapabilir.")
        return

    cursor.execute("SELECT barracks, castle, army, gold FROM kingdoms WHERE group_id=?", (group_id,))
    kingdom = cursor.fetchone()

    # Debug: Veritabanından dönen sonuçları kontrol et
    print(f"Veritabanından dönen krallık verisi: {kingdom}")

    if kingdom:
        # Verinin beklenen boyutta olup olmadığını kontrol et
        if len(kingdom) != 4:
            await message.reply("Krallık verileri beklenenden farklı. Lütfen veritabanı şemasını kontrol edin.")
            return

        if upgrade_type == 'kışla' and kingdom[0] < 10 and kingdom[3] >= 50000:
            cursor.execute("UPDATE kingdoms SET barracks = barracks + 1, gold = gold - 50000 WHERE group_id=?", (group_id,))
        elif upgrade_type == 'kale' and kingdom[1] < 10 and kingdom[3] >= 100000:
            cursor.execute("UPDATE kingdoms SET castle = castle + 1, gold = gold - 100000 WHERE group_id=?", (group_id,))
        elif upgrade_type == 'ordu' and kingdom[2] < 500 and kingdom[3] >= 75000:
            cursor.execute("UPDATE kingdoms SET army = army + 50, gold = gold - 75000 WHERE group_id=?", (group_id,))
        else:
            await message.reply("Yetersiz altın veya yükseltme limiti aşıldı.")
            return

        conn.commit()
        await message.reply(f"{upgrade_type.capitalize()} başarıyla yükseltildi!")
    else:
        await message.reply("Önce krallığınızı oluşturmalısınız.")
        
        
        
@bot.on_message(filters.command('savas'))
async def attack_kingdom(client, message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Kullanım: /savas [krallık ID]")
        return

    target_group_id = int(args[1])
    attacker_group_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(user_id, attacker_group_id):
        await message.reply("Yalnızca yöneticiler saldırı başlatabilir.")
        return

    cursor.execute("SELECT name, army, gold FROM kingdoms WHERE group_id=?", (attacker_group_id,))
    attacker_kingdom = cursor.fetchone()
    cursor.execute("SELECT name, army, gold FROM kingdoms WHERE group_id=?", (target_group_id,))
    target_kingdom = cursor.fetchone()

    if not attacker_kingdom:
        await message.reply("Krallığınızı önce oluşturmalısınız.")
        return

    if not target_kingdom:
        await message.reply("Hedef krallık bulunamadı.")
        return

    attacker_name, attacker_army, attacker_gold = attacker_kingdom
    target_name, target_army, target_gold = target_kingdom
    stolen_gold = int(target_gold * 0.5)  # Çalınan altın miktarı

    await message.reply(f"Savaş başladı! ⚔️ İyi olan kazansın")
    await client.send_animation(target_group_id, 
                                animation=f"https://graph.org/file/d8703a439b12d03645969.gif",
                                caption = f"{attacker_name} krallığı size savaş açtı! ⚔️ İyi olan kazansın..."
                                )

    await asyncio.sleep(60)  # 60 saniye bekleme

    if attacker_army > target_army:
        # Saldırı başarılı
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id=?", (stolen_gold, attacker_group_id))
        cursor.execute("UPDATE kingdoms SET gold = gold - ? WHERE group_id=?", (stolen_gold, target_group_id))
        conn.commit()
        await client.send_animation(attacker_group_id,
                                    animation=f"https://graph.org/file/36b7966eb7fd1891f15ca.gif", 
                                    caption=f"🎉 Saldırı başarılı! {target_name} krallığından {stolen_gold} altın çalındı. 🎉"
                                    )
        await client.send_animation(target_group_id, 
                                  animation="https://graph.org/file/fe560118a0e57104522af.gif",
                                  caption=f"{attacker_name} krallığı size saldırdı ve {stolen_gold} altın çaldı! Kaybettiniz."
                                  )
    elif attacker_army == target_army:
        # Berabere
        await client.send_message(attacker_group_id, f"{attacker_name} ve {target_name} krallıkları arasında yapılan savaş berabere sonuçlandı.")
        await client.send_message(target_group_id, f"{attacker_name} krallığı ile savaşınız berabere bitti.")
    else:
        # Saldırı başarısız
        await client.send_animation(attacker_group_id,
                                    animation=f"https://graph.org/file/fe560118a0e57104522af.gif",
                                    caption=f"Saldırı başarısız! {target_name} krallığının savunması çok güçlü."
                                    )
        await client.send_animation(target_group_id, 
                                  animation=f"https://graph.org/file/36b7966eb7fd1891f15ca.gif",
                                  caption=f"{attacker_name} krallığı size saldırdı ama savunmanız başarılı oldu! Kazandınız."
                                  )
        


@bot.on_message(filters.command('analiz'))
async def analyze_kingdoms(client, message):
    group_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(user_id, group_id):
        await message.reply("Bu komutu kullanma yetkiniz yok.")
        return

    cursor.execute("SELECT group_id, name FROM kingdoms")
    kingdoms = cursor.fetchall()
    
    if not kingdoms:
        await message.reply("Krallık verileri bulunamadı.")
        return

    last_kingdom = getattr(client, 'last_analyzed_kingdom', None)
    available_kingdoms = [k for k in kingdoms if k[0] != last_kingdom]
    
    if not available_kingdoms:
        await message.reply("Tüm krallıklar analiz edildi.")
        return
    
    kingdom = random.choice(available_kingdoms)
    cursor.execute("SELECT barracks, castle, army, gold FROM kingdoms WHERE group_id=?", (kingdom[0],))
    kingdom_data = cursor.fetchone()

    response = (
        f"Krallık ID: `{kingdom[0]}`\n"
        f"Krallık Adı: {kingdom[1]}\n"
        f"Kışla: {kingdom_data[0]}\n"
        f"Kale: {kingdom_data[1]}\n"
        f"Ordu: {kingdom_data[2]}\n"
        f"Altın: {kingdom_data[3]}"
    )

    await message.reply(response)
    client.last_analyzed_kingdom = kingdom[0]


@bot.on_message(filters.command('slot'))
async def slot_game(client, message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Kullanım: /slot [miktar]")
        return

    amount = int(args[1])
    group_id = message.chat.id
    user_id = message.from_user.id

    # Kullanıcının krallıktaki altın miktarını kontrol et
    cursor.execute("SELECT gold FROM members WHERE user_id = ? AND group_id = ?", (user_id, group_id))
    user_gold = cursor.fetchone()
    if not user_gold or user_gold[0] < amount:
        await message.reply("Yetersiz altın.")
        return

    # Slot oyunu
    symbols = ['🍒', '🍋', '🍊']
    result = [random.choice(symbols) for _ in range(3)]
    await message.reply("Slot sonuçları: " + " ".join(result))

    # Kazanma durumunu kontrol et
    if result[0] == result[1] == result[2]:  # 3 sembol eşleşirse
        prize = amount * 1.75
        tax = prize * 0.25
        net_prize = prize - tax
        cursor.execute("UPDATE members SET gold = gold + ? WHERE user_id = ? AND group_id = ?", (net_prize, user_id, group_id))
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id=?", (tax, group_id))
        cursor.execute("UPDATE members SET gold = gold - ? WHERE user_id = ? AND group_id = ?", (amount, user_id, group_id))
        conn.commit()
        await message.reply(f"Tebrikler! Üç sembol eşleşti! Kazancınız: {net_prize} altın. {tax} altını vergi olarak kesildi.")
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:  # 2 sembol eşleşirse
        prize = amount * 0.75
        tax = amount * 0.25
        cursor.execute("UPDATE members SET gold = gold + ? WHERE user_id = ? AND group_id = ?", (prize, user_id, group_id))
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id=?", (tax, group_id))
        cursor.execute("UPDATE members SET gold = gold - ? WHERE user_id = ? AND group_id = ?", (amount, user_id, group_id))
        conn.commit()
        await message.reply(f"İki sembol eşleşti! Kazancınız: {prize} altın. {tax} altını vergi olarak kesildi.")
    else:  # Hiçbir sembol eşleşmezse
        tax = amount * 0.05
        cursor.execute("UPDATE members SET gold = gold - ? WHERE user_id = ? AND group_id = ?", (amount, user_id, group_id))
        cursor.execute("UPDATE kingdoms SET gold = gold + ? WHERE group_id=?", (tax, group_id))
        conn.commit()
        await message.reply(f"Kumarda kaybeden aşkta kazanır yeğen, bakiye {amount} altının {tax} altını vergi olarak kralla ödeme yapıldı.")

@bot.on_message(filters.command('bakiyem'))
async def check_balance(client, message):
    user_id = message.from_user.id
    group_id = message.chat.id

    cursor.execute("SELECT gold FROM members WHERE user_id = ? AND group_id = ?", (user_id, group_id))
    user_gold = cursor.fetchone()
    if user_gold:
        await message.reply(f"👛 Mevcut bakiyeniz: {user_gold[0]} altın.")
    else:
        await message.reply("Bakiyeniz bulunamadı.")
        
if bot:
    bot.start()
print("Bot Aktif @PlutoKanal - @AnonimYazar")
idle()

