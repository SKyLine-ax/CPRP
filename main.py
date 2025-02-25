import discord
from discord.ext import commands
import sqlite3
import asyncio
import random
import datetime
import sqlite3
import os
import re
import json
import time
import concurrent.futures
import aiosqlite
import json
from discord import member
from datetime import datetime, timedelta
from discord import Embed
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput
import sys
from dotenv import load_dotenv

ALLOWED_CHANNELS = {
    "collect": 1330156658961158164,
    "pay": 1330156658961158164,
    "shop": 1330156658961158164,
    "create_item":1152564292932087809,
    "buy": 1151600202696884257,
    "date": 1154910934687551508,  
    "season": 1154910638531956826,  
    "end_season": 1154911455808864388,  
    "community": 1215709201196781638
}


COMMAND_ROLES = {
    "add_money": [1151900573524836395, 1151516441267417129, 1151552603147218945],
    "create_promo": [1151900573524836395, 1151516441267417129],
    "delete_promo": [1151900573524836395, 1151516441267417129],
    "h_promo": [1151900573524836395, 1151516441267417129],
    "promo": [1151552605034643587],
    "create_item": [1151597048374759484, 1159779908491415662, 1151516441267417129, 1151900573524836395],
    "delete_item": [1159779908491415662, 1151516441267417129, 1151900573524836395, 1151552603147218945],
    "take_item": [1151516441267417129, 1151900573524836395, 1151552603147218945, 1159779908491415662],
    "date": [1151516441267417129, 1151900573524836395],
    "season": [1151516441267417129, 1151900573524836395],
    "end_se": [1151516441267417129, 1151900573524836395]
}

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True


bot = commands.Bot(command_prefix='!', intents=intents)


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_PATH = 'central.db'

conn = sqlite3.connect('central.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY, 
    nickname TEXT NOT NULL,
    balance INTEGER DEFAULT 0,
    ideology TEXT DEFAULT 'Отсутствует',
    religion TEXT DEFAULT 'Отсутствует',
    government TEXT DEFAULT 'Отсутствует',
    role TEXT DEFAULT 'None', 
    eco INTEGER DEFAULT 0,
    army TEXT DEFAULT 'Военная Мощь: Слабая'
);
''') 

conn.commit()  

cursor.execute("""
CREATE TABLE IF NOT EXISTS guild_data (
    guild_id INTEGER PRIMARY KEY,
    date INTEGER DEFAULT 0,
    season INTEGER DEFAULT 0,
    end_season INTEGER DEFAULT 0,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
conn.close




cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Таблицы в базе данных:", tables)




def ensure_cooldowns_table():
    with sqlite3.connect('central.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_used TEXT
        )
        """)
        conn.commit()


ensure_cooldowns_table()




def initialize_database():
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            country_emoji TEXT,
            equipment_emoji TEXT,
            role_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()


initialize_database()



cursor.execute("""
CREATE TABLE IF NOT EXISTS inv (
    user_id TEXT,
    item_name TEXT,
    quantity INTEGER,
    country_emoji TEXT,
    equipment_emoji TEXT,
    description TEXT
)
""")
conn.commit()
conn.close()



@bot.event
async def on_command(ctx):
    """Глобальная проверка канала для всех команд."""
    command_name = ctx.command.name  
    

    excluded_commands = {"date", "season", "end_se"}
    if command_name in excluded_commands:
        return  


    allowed_channel_id = ALLOWED_CHANNELS.get(command_name)
    if allowed_channel_id and ctx.channel.id != allowed_channel_id:
        allowed_channel = bot.get_channel(allowed_channel_id)
        embed = discord.Embed(
            title="⚠️ Ошибка",
            description=f"<a:no:1330115448766988288> Эта команда доступна только в {allowed_channel.mention}.",
            color=0x3498db
        )
        await ctx.send(embed=embed)



def has_role_for_command():
    async def predicate(ctx):

        command_name = ctx.command.name
        allowed_roles = COMMAND_ROLES.get(command_name, [])


        return any(role.id in allowed_roles for role in ctx.author.roles)
    return commands.check(predicate)


@bot.event
async def on_command_error(ctx, error):
    try:
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="⚠️ Ошибка",
                description="<a:no:1330115448766988288> У вас не достаточно прав для выполнения этой команды.",
                color=discord.Color.from_rgb(128, 128, 128)
            )
    except Exception as e:
        print(f"Ошибка обработки ошибки: {e}")

    await ctx.send(embed=embed)



ITEMS_PER_PAGE = 10
user_pages = {}


@bot.event
async def on_ready():
    activity = discord.Game(name="Country Politican RP")
    await bot.change_presence(activity=activity)


    print(f"Бот подключён как {bot.user}. ЯВЛЯЕТСЯ СОБСТВЕННОСТЬЮ Country Politican RP")
    if not daily_update.is_running():
        daily_update.start()
    if not update_community_channel.is_running():
        update_community_channel.start()



@bot.command()
async def check_id(ctx, member: discord.Member):

    member_id = member.id
    

    await ctx.send(f"**ID игрока** {member.mention}:`{member_id}`")
    

    await ctx.send(str(member_id))





class InvView(discord.ui.View):
    def __init__(self, author_id: int, items: list, current_page: int):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.items = items
        self.current_page = current_page


        total_pages = (len(self.items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= total_pages

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Вы не можете взаимодействовать с инвентарём другого игрока.", ephemeral=True)
            return

        if self.current_page > 1:
            self.current_page -= 1
            await self.update_inventory(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Вы не можете взаимодействовать с инвентарём другого игрока.", ephemeral=True)
            return

        total_pages = (len(self.items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        if self.current_page < total_pages:
            self.current_page += 1
            await self.update_inventory(interaction)

    async def update_inventory(self, interaction: discord.Interaction):
        start_index = (self.current_page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        page_items = self.items[start_index:end_index]

        embed = discord.Embed(
            title="Инвентарь игрока",
            description="Вот что есть в инвентаре:",
            color=discord.Color.from_rgb(143, 188, 143)
        )
        embed.add_field(name="", value="\n".join(page_items) if page_items else "Инвентарь пуст.", inline=False)

        total_pages = (len(self.items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= total_pages

        embed.set_footer(text=f"Страница {self.current_page}/{total_pages}  •  Всего предметов: {len(self.items)}")

        await interaction.response.edit_message(embed=embed, view=self)


@bot.command()
async def inv(ctx, member: discord.Member = None):
    """Показывает инвентарь игрока с эмодзи стран и техники, а также описанием."""
    target = member if member else ctx.author
    user_id = str(target.id)


    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()


    cursor.execute("""
        SELECT country_emoji, equipment_emoji, item_name, quantity, description
        FROM inv
        WHERE user_id = ?
    """, (user_id,))
    inventory = cursor.fetchall()


    conn.close()


    items_list = [
        f'{item[0] or "❓"} {item[1] or "❓"} **{item[2] or "Неизвестный предмет"}** | {item[3] or 0} шт.\n{item[4] or "Нет описания,обратитесь к руководству проекта за информацией."}'
        for item in inventory
    ]


    embed = discord.Embed(
        description="",
        color=discord.Color.from_rgb(143, 188, 143)
    )
    embed.set_author(
        name=f"Инвентарь игрока {target.display_name}",
        icon_url=target.avatar.url if target.avatar else target.default_avatar.url
    )

    if not items_list:
        embed.add_field(name="", value="Инвентарь пуст.", inline=False)
        embed.set_footer(text="Страница 1/1 • Всего предметов: 0")
    else:

        total_pages = (len(items_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page_items = items_list[:ITEMS_PER_PAGE]
        embed.add_field(name="", value="\n".join(page_items), inline=False)
        embed.set_footer(text=f"Страница 1/{total_pages} • Всего предметов: {len(items_list)}")


    view = InvView(author_id=ctx.author.id, items=items_list, current_page=1)
    await ctx.send(embed=embed, view=view)


@bot.command()
async def collect(ctx):
    user_id = ctx.author.id
    user_name = ctx.author.display_name  
    user_avatar = ctx.author.avatar.url  
    earnings = 100  
    cooldown_time = timedelta(hours=1)  
    user = ctx.author  
    user_avatar = user.avatar.url


    allowed_channel_id = ALLOWED_CHANNELS.get("collect")
    if allowed_channel_id is None:
        await ctx.send("Ошибка конфигурации: ID разрешённого канала не задан.")
        return


    if ctx.channel.id != allowed_channel_id:
        return  

    try:
        with sqlite3.connect('central.db') as conn:
            cursor = conn.cursor()


            cursor.execute("SELECT last_used FROM cooldowns WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if result and result[0]:
                last_used = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
                remaining_time = (last_used + cooldown_time) - datetime.now()

                if remaining_time > timedelta(0):
                    hours, remainder = divmod(remaining_time.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    embed = discord.Embed(
                        description=f"<a:no:1330115448766988288> Подождите, вы уже использовали collect. Следующий collect через: **{hours} ч {minutes} мин.**",
                        color=discord.Color.from_rgb(47, 49, 54)
                    )
                    await ctx.send(embed=embed)
                    return


            cursor.execute("SELECT balance FROM players WHERE id = ?", (user_id,))
            result = cursor.fetchone()

            if result:
                new_balance = result[0] + earnings
                cursor.execute("UPDATE players SET balance = ? WHERE id = ?", (new_balance, user_id))
                conn.commit()

                embed = discord.Embed(
                    title=f"Обновление бюджета — {user_name}",
                    description=f"<:emoji_74:1330508247781867632> Бюджет был пополнен! Сейчас он составляет: **{new_balance:,} $**",
                    color=discord.Color.from_rgb(47, 49, 54)
                )
                embed.set_footer(icon_url=ctx.author.avatar.url) 
                embed.add_field(name="Получено:", value=f"**{earnings:,} $**", inline=True)  
                await ctx.send(embed=embed)
            else:
                await ctx.send("Вы не зарегистрированы.")
                return


            cursor.execute("""
            INSERT INTO cooldowns (user_id, last_used) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET last_used = ?;
            """, (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    except sqlite3.Error as e:
        await ctx.send("Произошла ошибка при работе с базой данных. Пожалуйста, попробуйте позже.")
        print(f"Database error: {e}")



ROLE_IDS = {
    1: [1155087695891136573, 1156155732429910046, 1151552605034643587],  
    2: [1156155601940910132, 1156155732429910046, 1151552605034643587],  
    3: [1155087463056941126, 1156155732429910046, 1151552605034643587]   
}

UNREGISTERED_ROLE_ID = 1151598722791252009  
CURATOR_ROLE_ID = 1151900573524836395       
REGISTERED_ROLE_ID = 1151552605034643587


ROLE_NAMES = {
    1: "Страна/Регион",
    2: "ЧВК",
    3: "Повстанческое Движение"
}

@bot.command()
async def reg(ctx, member: discord.Member):
    guild = ctx.guild


    curator_role = guild.get_role(CURATOR_ROLE_ID)
    if not curator_role:
        await ctx.send("Роль 'Куратор' не найдена на сервере.")
        return

    if curator_role not in ctx.author.roles:
        await ctx.send("<a:no:1330115448766988288> У вас нет прав для выполнения этой команды.")
        return



    registered_role = guild.get_role(REGISTERED_ROLE_ID)
    if registered_role in member.roles:
        embed = discord.Embed(
            title="⚠️ Ошибка",
            description=f"<a:no:1330115448766988288> Игрок {member.mention} уже зарегистрирован!",
            color=discord.Color.from_rgb(189, 183, 107)
        )
        await ctx.send(embed=embed)  
        return



    embed = discord.Embed(
        title="Регистрация",
        description=(
            "Выберите, за кого вы хотите зарегистрировать игрока:\n"
            "1. Страна/Регион\n"
            "2. ЧВК\n"
            "3. Повстанец"
        ),
        color=discord.Color.from_rgb(189, 183, 107)
    )
    embed.set_footer(text=f"Регистрацию проводит: {ctx.author}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


    def check(msg):
        return (
            msg.author == ctx.author  
            and msg.channel == ctx.channel  
            and msg.content.isdigit()  
            and int(msg.content) in ROLE_IDS  
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=60.0)
        role_choice = int(msg.content)
    except asyncio.TimeoutError:
        await ctx.send("Время вышло! Повторите команду для регистрации.")
        return


    selected_roles_ids = ROLE_IDS[role_choice]
    selected_roles = [guild.get_role(role_id) for role_id in selected_roles_ids]
    unregistered_role = guild.get_role(UNREGISTERED_ROLE_ID)


    if not all(selected_roles):
        await ctx.send("Одна или несколько ролей не найдены на сервере. Проверьте ID ролей.")
        return
    if not unregistered_role:
        await ctx.send(f"Роль с ID {UNREGISTERED_ROLE_ID} не найдена на сервере.")
        return

    # Назначаем игроку выбранные роли и удаляем роль "Не зарегистрирован"
    await member.add_roles(*selected_roles)
    await member.remove_roles(unregistered_role)

    # Получаем название роли для базы данных и ЛС
    role_name = ROLE_NAMES[role_choice]

    # Обновляем данные в базе данных
    try:
        with sqlite3.connect('central.db') as conn:
            cursor = conn.cursor()

            # Проверяем, есть ли уже игрок в таблице
            cursor.execute("SELECT id FROM players WHERE id = ?", (member.id,))
            result = cursor.fetchone()

            if result:
                # Если игрок уже есть, обновляем его информацию
                cursor.execute(
                    "UPDATE players SET nickname = ?, role = ? WHERE id = ?",
                    (member.name, role_name, member.id)
                )
            else:
                # Если игрока нет, добавляем новую запись
                cursor.execute(
                    "INSERT INTO players (id, nickname, role) VALUES (?, ?, ?)",
                    (member.id, member.name, role_name)
                )
            conn.commit()

    except sqlite3.Error as e:
        await ctx.send("Произошла ошибка при работе с базой данных.")
        print(f"Database error: {e}")
        return

    # Сообщение в общий чат
    await ctx.send(f"Игрок {member.mention} успешно зарегистрирован за: **{role_name}**!")

    # Сообщение в ЛС игроку
    embed_dm = discord.Embed(
        title="Вы успешно прошли регистрацию на Country Politician RP!",
        description=(f"Вы зарегистрированы за: **{role_name}**. Приятной игры! :)\n\n **Нашли неполадку в работе бота?** [[Сообщить о проблеме]]""(https://discord.com/channels/1151515420080209940/1151898768636133468)"),
        color=discord.Color.from_rgb(189, 183, 107)
    )
    embed_dm.set_footer(text=f"Регистрацию провёл: {ctx.author}", icon_url=ctx.author.avatar.url)

    try:
        await member.send(embed=embed_dm)
    except discord.Forbidden:
        await ctx.send(f"Не удалось отправить сообщение в ЛС {member.mention}. Проверьте настройки Discord.")



@bot.command()
@has_role_for_command()
async def add_money(ctx, member: discord.Member = None, amount: int = None, *, reason: str = None):
    """
    Добавляет деньги указанному игроку.
    :param member: discord.Member - игрок, которому нужно выдать деньги.
    :param amount: int - сумма выдачи.
    :param reason: str - причина выдачи.
    """
    if not member or amount is None or not reason:
        # Если один из параметров отсутствует
        await ctx.send("**Вы не указали пинг игрока, сумму выдачи или причину выдачи.**")
        return

    if amount <= 0:
        # Проверяем, чтобы сумма была положительной
        await ctx.send("**Сумма выдачи должна быть больше нуля.**")
        return

    conn = sqlite3.connect('central.db')  
    cursor = conn.cursor()

    # Проверяем, существует ли игрок в базе данных по полю id
    cursor.execute("SELECT balance FROM players WHERE id=?", (member.id,))
    user_data = cursor.fetchone()

    if not user_data:
        # Если игрока нет в базе
        await ctx.send(f"Игрок {member.mention} не найден в базе данных.")
    else:
        # Обновляем баланс игрока
        new_balance = user_data[0] + amount
        cursor.execute("UPDATE players SET balance=? WHERE id=?", (new_balance, member.id))
        conn.commit()

        # Сообщение об успешном обновлении
        embed = discord.Embed(
            title="Выдача средств",
            description=f"Баланс игрока {member.mention} обновлён!",
            color=discord.Color.green()
        )
        embed.add_field(name="Сумма выдачи", value=f"{amount} $", inline=True)
        embed.add_field(name="Причина выдачи", value=reason, inline=True)
        embed.add_field(name="Новый баланс", value=f"{new_balance} $", inline=False)
        embed.set_footer(text=f"Выдал: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    conn.close()



@bot.command()
async def pay(ctx, member: discord.Member = None, amount: float = None):
    """Команда для перевода денег между игроками."""
    
    # Проверяем, что команда вызвана в разрешённом канале
    allowed_channel_id = ALLOWED_CHANNELS.get("pay")
    if ctx.channel.id != allowed_channel_id:
        allowed_channel = bot.get_channel(allowed_channel_id)
        return
    
    # Проверяем, что игрок указал пинг и сумму
    if not member or not amount:
        embed = discord.Embed(
            title="⚠️ Ошибка",
            description="Пожалуйста, укажите игрока и сумму перевода.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Проверяем, что игрок не переводит деньги самому себе
    if member.id == ctx.author.id:
        embed = discord.Embed(
            title="⚠️ Ошибка",
            description="Вы не можете перевести деньги самому себе.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Округляем сумму до целого числа
    amount = int(amount)


    conn = sqlite3.connect('central.db')
    cursor = conn.cursor()

    # Получаем баланс инициатора
    cursor.execute("SELECT balance FROM players WHERE id = ?", (ctx.author.id,))
    result = cursor.fetchone()

    if result:
        sender_balance = result[0]

        # Проверяем, достаточно ли средств у отправителя
        if sender_balance < amount:
            embed = discord.Embed(
                title="⚠️ Ошибка",
                description="У вас недостаточно средств для перевода.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        # Получаем баланс получателя
        cursor.execute("SELECT balance FROM players WHERE id = ?", (member.id,))
        result = cursor.fetchone()

        if result:
            receiver_balance = result[0]

            # Выполняем перевод
            new_sender_balance = sender_balance - amount
            new_receiver_balance = receiver_balance + amount

            # Обновляем балансы в бд
            cursor.execute("UPDATE players SET balance = ? WHERE id = ?", (new_sender_balance, ctx.author.id))
            cursor.execute("UPDATE players SET balance = ? WHERE id = ?", (new_receiver_balance, member.id))
            conn.commit()

            # Отправляем 
            embed = discord.Embed(
                title="💰 Перевод успешен",
                description=f"**{ctx.author.name}** успешно перевел **{amount}$** игроку **{member.name}**.",
                color=discord.Color.from_rgb(106, 90, 205)
            )
            embed.add_field(name="", value="Комиссия составила 0%", inline=True)
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"Игрок {member.name} не найден в базе данных.")

    else:
        await ctx.send("Вы не зарегистрированы.")

    conn.close()



promo_file = "promo.json"
users_file = "users.json"

# сейв промо
def load_promos():
    if os.path.exists(promo_file):
        with open(promo_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_promos(promos):
    with open(promo_file, "w", encoding="utf-8") as f:
        json.dump(promos, f, ensure_ascii=False, indent=4)

# сейв данные юзеров
def load_users():
    if os.path.exists(users_file):
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# загрузка данных
promos = load_promos()
users = load_users()


# парсинг времени
def parse_time(time_str):
    time_pattern = re.compile(r'(?:(\d+)д)?(?:(\d+)ч)?(?:(\d+)мин)?(?:(\d+)сек)?')
    match = time_pattern.match(time_str)

    if not match:
        return None

    days, hours, minutes, seconds = match.groups()
    total_seconds = 0
    if days:
        total_seconds += int(days) * 86400
    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)

    return total_seconds

# форматирование времени
def format_time(seconds):
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    time_str = []
    if days > 0:
        time_str.append(f"{days}д")
    if hours > 0:
        time_str.append(f"{hours}ч")
    if minutes > 0:
        time_str.append(f"{minutes}мин")
    if seconds > 0:
        time_str.append(f"{seconds}сек")

    return " ".join(time_str) if time_str else "0сек"

@bot.command()
@has_role_for_command()
async def create_promo(ctx, code: str = None, amount: int = None, cooldown: str = "0сек", uses: str = "1"):
    if not code or amount is None:
        await ctx.send("Вы не указали название промокода, сумму или время использования. Формат команды: **!create_promo <название> <сумма> [время] <количество использований>**.")
        return

    cooldown_seconds = parse_time(cooldown)
    if cooldown_seconds is None:
        await ctx.send("Неверный формат времени. Используйте формат: **Xд Xч Xмин Xсек.**")
        return

    if uses == "~":
        uses = -1  # Значение -1 будет означать не ограниченные юзы
    else:
        try:
            uses = int(uses)
        except ValueError:
            await ctx.send("Неверное значение для количества использований. **Используйте целое число или символ ~ для неограниченного количества.**")
            return

    if code in promos:
        await ctx.send(f"Промокод **{code}** уже существует.")
        return

    promos[code] = {
        "amount": amount,
        "uses": uses,
        "cooldown": cooldown_seconds
    }

    save_promos(promos)
    embed= discord.Embed (
        description=f"<:emoji_77:1330875368575602740> Промокод **{code}** успешно создан с количеством {amount}, сроком годности {cooldown} и {uses if uses != -1 else 'неограниченным'} количеством использований.",
        color=discord.Color.from_rgb(47, 49, 54)
    )
    await ctx.send(embed=embed)


@bot.command()
@has_role_for_command()
async def delete_promo(ctx):
    if not promos:
        embed = discord.Embed (
            title="⚠️Ошибка",
            description="<:emoji_78:1330878851273982033> Похоже промокодов еще нет,загляните позже.",
            color=discord.Color.from_rgb(106, 90, 205)
        )   
    
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="Удаление промокодов", description="Нажмите на кнопку, чтобы удалить промокод.", color=discord.Color.from_rgb(106, 90, 205))
    view = View()

    for code in list(promos.keys()):
        button = Button(label=code, style=discord.ButtonStyle.red)

        async def button_callback(interaction, code=code):
            promos.pop(code, None)
            save_promos(promos)
            await interaction.response.send_message(f"Промокод `{code}` успешно удалён.", ephemeral=True)

        button.callback = button_callback
        view.add_item(button)

    await ctx.send(embed=embed, view=view)

@bot.command()
@has_role_for_command()
async def h_promo(ctx):
    if not promos:
        await ctx.send("История промокодов пуста!")
        return

    embed = discord.Embed(title="История промокодов", color=discord.Color.from_rgb(47, 49, 54))

    for code, details in promos.items():
        embed.add_field(
            name=f"Код: {code}",
            value=(f"Сумма: {details['amount']}\n"
                   f"Использований: {details['uses']}\n"
                   f"Ожидание: {format_time(details['cooldown'])}"),
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command()
@has_role_for_command()
async def promo(ctx, code: str = None):
    """Обработка промокодов"""
    user_id = str(ctx.author.id)
    restricted_role_id = 1151598722791252009  # ID роли плеер

    # Проверка на наличие запрещенной роли
    if any(role.id == restricted_role_id for role in ctx.author.roles):
        embed= discord.Embed(
            description="<a:no:1330115448766988288> Вы не зарегестрированы",
            color=discord.Color.from_rgb(47, 49, 54)
        )

        await ctx.send(embed=embed)
        return


    if not code:
         embed= discord.Embed(
            description="<a:no:1330115448766988288> Вы не указали промокод.Используйте !promo (название промокода)",
            color=discord.Color.from_rgb(47, 49, 54)
        )

    await ctx.send(embed=embed)
    return


    # есть ли код в JSON
    if code not in promos:
        await ctx.send("Промокод не найден.")
        return

    # использовал ли уже этот юзер данный промокод
    if user_id in users and code in users[user_id]:
        await ctx.send(f"Вы уже использовали промокод `{code}`.")
        return

    # Получаем инфу о промо
    promo_data = promos[code]
    amount = promo_data["amount"]
    uses = promo_data["uses"]
    cooldown = promo_data["cooldown"]

    # Проверяем не исчерпаны ли юзы промокода
    if uses == 0:
        await ctx.send(f"Промокод `{code}` больше недоступен.")
        return
    elif uses > 0:
        promos[code]["uses"] -= 1
    # для неограниченного промокода просто не уменьшаем uses

    # Обновляем данные юзера для сейва того что он уже юзнул промокод
    if user_id not in users:
        users[user_id] = []
    users[user_id].append(code)

    # Сохраняем обновленные данные
    save_promos(promos)
    save_users(users)

    # Сообщаем об успешном юзе
    embed = Embed(
        description=f"<a:yes:1330115480069083208> Вы успешно использовали промокод **{code}**. Вы получили **{amount}** $",
        color=discord.Color.from_rgb(47, 49, 54)
    )
    await ctx.send(embed=embed)



# ЭТА ЧАСТЬ НЕ РАБОТАЕТ!!!!
alliances = []

class AllianceView(View):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor
        self.conn = conn

        # Поля для ввода
        self.name = TextInput(label="Название альянса", placeholder="Введите название альянса")
        self.slogan = TextInput(label="Лозунг", placeholder="Введите лозунг альянса")

        # Добавляем их в модальное окно
        self.add_item(self.name)
        self.add_item(self.slogan)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value.strip()
        slogan = self.slogan.value.strip()
        user_id = interaction.user.id

        # Проверяем баланс игрока
        self.cursor.execute("SELECT balance FROM players WHERE id = ?", (user_id,))
        result = self.cursor.fetchone()

        if not result or result[0] < self.cost:
            await interaction.response.send_message(
                "У вас недостаточно средств для создания альянса.", ephemeral=True
            )
            return

        # Списываем средства
        new_balance = result[0] - self.cost
        self.cursor.execute("UPDATE players SET balance = ? WHERE id = ?", (new_balance, user_id))
        self.conn.commit()

        # Добавляем альянс в глобальный список
        new_alliance = {
            "name": name,
            "leader": interaction.user.name,
            "members": [interaction.user.name],
            "max_members": 10,
            "slogan": slogan,
            "level": 1,
            "status": "Открытый",
            "budget": 0
        }
        alliances.append(new_alliance)

        await interaction.response.send_message(
            f"Альянс **{name}** успешно создан!", ephemeral=True
        )


class AllianceView(View):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor
        self.conn = conn

    @discord.ui.button(label="Создать Альянс", style=discord.ButtonStyle.green)
    async def create_alliance(self, button: discord.ui.Button, interaction: discord.Interaction):
        cost = 1000  # Стоимость создания альянса
        modal = AllianceModal(interaction, cost, self.cursor, self.conn)
        await interaction.response.send_modal(modal)

@bot.command()
async def alliance(ctx):
    embed = discord.Embed(title="Список Альянсов", color=discord.Color.blue())
    # ...
    view = AllianceView(cursor, conn)
    await ctx.send(embed=embed, view=view)

    if alliances:
        for alliance in alliances:
            embed.add_field(
                name=f"• Союз: {alliance['name']}",
                value=(
                    f"Глава Союза: {alliance['leader']}\n"
                    f"Члены союза ({len(alliance['members'])}/{alliance['max_members']}): {', '.join(alliance['members'])}\n"
                    f"Лозунг: {alliance['slogan']}\n"
                    f"Уровень альянса: {alliance['level']}\n"
                    f"Состояние альянса: {alliance['status']}\n"
                    f"Бюджет: {alliance['budget']} $"
                ),
                inline=False
            )
    else:
        embed.description = "Пока что альянсы отсутствуют. Вы можете создать первый!"

    view = AllianceView(cursor, conn)
    await ctx.send(embed=embed, view=view)



@bot.command()
async def shop(ctx):
    allowed_channel_id = ALLOWED_CHANNELS.get("shop")
    if ctx.channel.id != allowed_channel_id:
        return


    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    # Получаем все товары из таблицы shop
    cursor.execute("SELECT name, price, description, country_emoji, equipment_emoji FROM shop")
    shop_items = cursor.fetchall()
    conn.close()

    if not shop_items:
        embed = discord.Embed(
            title="<:emoji_79:1330937253148491827> Магазин техники",
            description="<a:no:1330115448766988288> В магазине нет техники, попробуйте позже.",
            color=discord.Color.from_rgb(47, 79, 79),
        )
        await ctx.send(embed=embed)
        return

    user_pages[ctx.author.id] = 0
    await send_shop_page(ctx, ctx.author.id, shop_items)

async def send_shop_page(ctx_or_interaction, user_id, shop_items):
    is_interaction = hasattr(ctx_or_interaction, "response")
    page = user_pages.get(user_id, 0)
    start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    items = shop_items[start:end]

    if not items:
        embed = discord.Embed(
            title="<:emoji_79:1330937253148491827> Магазин техники",
            description="Нет доступной техники на данной странице.",
            color=discord.Color.red(),
        )
        if is_interaction:
            await ctx_or_interaction.response.edit_message(embed=embed, view=None)
        else:
            await ctx_or_interaction.send(embed=embed)
        return

    total_pages = (len(shop_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    embed = discord.Embed(
        title="<:emoji_79:1330937253148491827> Магазин техники",
        description="Выберите технику для покупки:",
        color=discord.Color.from_rgb(47, 79, 79),
    )

    for item in items:
        name, price, description, country_emoji, equipment_emoji = item
        embed.add_field(
            name=f"{country_emoji or ''} {equipment_emoji or ''} {name} - {price:,}$",
            value=description or "Описание недоступно.",
            inline=False,
        )

    embed.set_footer(text=f"Страница: {page + 1}/{total_pages}")

    view = View()
    view.add_item(Button(label="⇐", style=discord.ButtonStyle.gray, custom_id=f"prev_{user_id}", disabled=page == 0))
    view.add_item(Button(label="⇒", style=discord.ButtonStyle.gray, custom_id=f"next_{user_id}", disabled=end >= len(shop_items)))

    if is_interaction:
        await ctx_or_interaction.response.edit_message(embed=embed, view=view)
    else:
        await ctx_or_interaction.send(embed=embed, view=view)

@bot.event
async def on_interaction(interaction):
    user_id = interaction.user.id

    if user_id not in user_pages:
        await interaction.response.send_message("Пожалуйста, сначала вызовите команду `!shop`.", ephemeral=True)
        return

    custom_id = interaction.data.get("custom_id")
    if custom_id.startswith("prev_"):
        user_pages[user_id] = max(0, user_pages[user_id] - 1)
    elif custom_id.startswith("next_"):
        user_pages[user_id] += 1

    # Подключаемся к базе данных для обновления итема
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description, country_emoji, equipment_emoji FROM shop")
    shop_items = cursor.fetchall()
    conn.close()

    await send_shop_page(interaction, user_id, shop_items)


@bot.command()
async def buy(ctx, item_name: str, quantity: str = "1"):
    """Покупка предметов из магазина по названию с проверкой ролей."""

    allowed_channel_id = ALLOWED_CHANNELS.get("buy")
    if allowed_channel_id is None:
        await ctx.send("Ошибка конфигурации: ID разрешённого канала не задан.")
        return 

    if ctx.channel.id != allowed_channel_id:
        return

    try:
        quantity = int(quantity)
    except ValueError:
        await ctx.send("<a:no:1330115448766988288> Количество должно быть числом.")
        return

    if quantity <= 0:
        await ctx.send("<a:no:1330115448766988288> Количество должно быть больше нуля.")
        return

    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    user_id = str(ctx.author.id)
    cursor.execute("SELECT balance FROM players WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await ctx.send("<a:no:1330115448766988288> У вас нет данных игрока. Используйте команду для регистрации.")
        conn.close()
        return

    user_balance = result[0]

    # Получаем данные,рольку,эмодзи,название,цену,описание крч да?
    cursor.execute("SELECT name, price, country_emoji, equipment_emoji, description, role_id FROM shop WHERE name = ?", (item_name,))
    found_item = cursor.fetchone()

    if not found_item:
        await ctx.send("<a:no:1330115448766988288> Предмет не найден в магазине.")
        conn.close()
        return

    item_name, item_price, country_emoji, equipment_emoji, description, role_id = found_item
    total_cost = item_price * quantity

    # Проверяем нужную рольку
    if role_id:
        required_role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        if required_role and required_role not in ctx.author.roles:
            await ctx.send(f"<a:no:1330115448766988288> У вас нет необходимой роли `{required_role.name}` для покупки этого предмета.")
            conn.close()
            return

    if user_balance < total_cost:
        await ctx.send("<a:no:1330115448766988288> Недостаточно средств для покупки.")
        conn.close()
        return

    # Обновляем баланс юзера
    new_balance = user_balance - total_cost
    cursor.execute("UPDATE players SET balance = ? WHERE id = ?", (new_balance, user_id))
    conn.commit()

    # Добавляем итем в инв
    cursor.execute("SELECT quantity FROM inv WHERE user_id = ? AND item_name = ?", (user_id, item_name))
    inv_result = cursor.fetchone()

    if inv_result:
        new_quantity = inv_result[0] + quantity
        cursor.execute("UPDATE inv SET quantity = ? WHERE user_id = ? AND item_name = ?", (new_quantity, user_id, item_name))
    else:
        cursor.execute("INSERT INTO inv (user_id, item_name, quantity, country_emoji, equipment_emoji, description) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, item_name, quantity, country_emoji, equipment_emoji, description))

    conn.commit()
    conn.close()

    await ctx.send(embed=discord.Embed(
        title="Покупка успешна",
        description=f"Вы приобрели {quantity} {country_emoji} {equipment_emoji} {item_name} за {total_cost}.\n"
                    f"Ваш новый баланс: {new_balance}.",
        color=discord.Color.from_rgb(47, 49, 54)
    ))


@buy.error
async def buy_error(ctx, error):
    allowed_channel_id = ALLOWED_CHANNELS.get("buy")

    # Проверяем, что ошибка связана с отсутствием аргумента
    if isinstance(error, commands.MissingRequiredArgument):
        if ctx.channel.id == allowed_channel_id:
            await ctx.send(embed=discord.Embed(
                description="<a:no:1330115448766988288> Вы не указали название предмета. Пример: `!buy Т-80 Оплот`",
                color=discord.Color.from_rgb(47, 49, 54)
            ))



# Словарь для отслеживания сессий создания предметов
item_creation_sessions = {}

@bot.command()
@has_role_for_command()
async def create_item(ctx):
    """Команда для создания нового предмета в магазине."""
    user_id = ctx.author.id

    # Проверяем чтобы куратор не создавал технику
    if user_id in item_creation_sessions:
        await ctx.send("Вы уже находитесь в процессе создания техника. Завершите текущий процесс или отмените его.")
        return

    # Инициализация новой сессии создания итема
    item_creation_sessions[user_id] = {
        "step": 1,  # Текущий шаг
        "data": {}  # Сюда сохраняются данные итема
    }

    await ctx.send(embed=discord.Embed(
        title="Создание техники",
        description="Укажите название техники.",
        color=discord.Color.from_rgb(47, 49, 54)
    ))

@bot.event
async def on_message(message):
    user_id = message.author.id

    # Проверяем, находится ли пользователь в процессе создания предмета
    if user_id not in item_creation_sessions:
        await bot.process_commands(message)
        return

    session = item_creation_sessions[user_id]
    step = session["step"]

    if step == 1:
        session["data"]["name"] = message.content.strip()
        session["step"] += 1
        await message.channel.send(embed=discord.Embed(
            title="Создание предмета",
            description="Укажите стоимость предмета (целое число).",
            color=discord.Color.from_rgb(47, 49, 54)
        ))

    elif step == 2:
        try:
            price = int(message.content.strip())
            if price <= 0:
                raise ValueError
            session["data"]["price"] = price
            session["step"] += 1
            await message.channel.send(embed=discord.Embed(
                title="Создание предмета",
                description="Укажите описание предмета.",
                color=discord.Color.from_rgb(47, 49, 54)
            ))
        except ValueError:
            await message.channel.send("Стоимость должна быть положительным целым числом. Попробуйте ещё раз.")

    elif step == 3:
        session["data"]["description"] = message.content.strip()
        session["step"] += 1
        await message.channel.send(embed=discord.Embed(
            title="Создание предмета",
            description="Укажите эмодзи страны (например, :flag_ua:).",
            color=discord.Color.from_rgb(47, 49, 54)
        ))

    elif step == 4:
        session["data"]["country_emoji"] = message.content.strip()
        session["step"] += 1
        await message.channel.send(embed=discord.Embed(
            title="Создание предмета",
            description="Укажите эмодзи техники (например, <:tank:12345>).",
            color=discord.Color.from_rgb(47, 49, 54)
        ))

    elif step == 5:
        session["data"]["equipment_emoji"] = message.content.strip()
        session["step"] += 1
        await message.channel.send(embed=discord.Embed(
            title="Создание предмета",
            description="Укажите роль страны, на которую регистрируете технику (упомяните роль).",
            color=discord.Color.from_rgb(47, 49, 54)
        ))

    elif step == 6:
        if len(message.role_mentions) != 1:
            await message.channel.send("Пожалуйста, упомяните ровно одну роль.")
            return

        role_id = message.role_mentions[0].id
        session["data"]["role_id"] = role_id

        # Подключаемся к базе данных и сохраняем предмет
        conn = sqlite3.connect("central.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO shop (name, price, description, country_emoji, equipment_emoji, role_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session["data"]["name"],
            session["data"]["price"],
            session["data"]["description"],
            session["data"]["country_emoji"],
            session["data"]["equipment_emoji"],
            session["data"]["role_id"]
        ))
        conn.commit()
        conn.close()

        await message.channel.send(embed=discord.Embed(
            title="Успешное создание",
            description=f"Предмет '{session['data']['name']}' успешно добавлен в магазин.",
            color=discord.Color.from_rgb(47, 49, 54)
        ))

        # Завершаем сессию
        del item_creation_sessions[user_id]

    await bot.process_commands(message)



@bot.command()
@has_role_for_command()
async def delete_item(ctx, item_name: str = None):
    """Удаление предмета из магазина по названию."""
    if not item_name:
        await ctx.send("<a:no:1330115448766988288> Вы не указали название предмета для удаления.")
        return


    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    # Проверяем, существует ли предмет в таблице магазина
    cursor.execute("SELECT name FROM shop WHERE name = ?", (item_name,))
    result = cursor.fetchone()

    if not result:
        await ctx.send("<a:no:1330115448766988288> Предмет с таким названием не найден в магазине.")
        conn.close()
        return

    # Удаляем предмет из базы данных
    cursor.execute("DELETE FROM shop WHERE name = ?", (item_name,))
    conn.commit()
    conn.close()

    embed= discord.Embed(
        description=f"<a:yes:1330115480069083208> Предмет '{item_name}' успешно удален из магазина.",
        color=discord.Color.from_rgb(47, 49, 54)
    )
    await ctx.send(embed=embed)



@bot.command()
async def use(ctx, item_name: str = None, quantity: str = "1"):
    """Использование предметов из инвентаря по названию и количеству."""
    
    if not item_name:
        await ctx.send("<a:no:1330115448766988288> Вы не указали название предмета для использования.")
        return

    try:
        # Преобразуем количество в число
        quantity = int(quantity)
    except ValueError:
        await ctx.send("<a:no:1330115448766988288> Количество должно быть числом.")
        return

    if quantity <= 0:
        await ctx.send("<a:no:1330115448766988288> Количество должно быть больше нуля.")
        return


    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    # Проверяем, есть ли игрок в таблице "players"
    user_id = str(ctx.author.id)
    cursor.execute("SELECT id FROM players WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await ctx.send("<a:no:1330115448766988288> У вас нет данных игрока. Используйте команду для регистрации.")
        conn.close()
        return

    # Проверяем, есть ли итем в инве игрока
    cursor.execute("""
    SELECT quantity FROM inv WHERE user_id = ? AND item_name = ?
    """, (user_id, item_name))
    inv_result = cursor.fetchone()

    if not inv_result:
        await ctx.send("<a:no:1330115448766988288> У вас нет такого предмета в инвентаре.")
        conn.close()
        return

    current_quantity = inv_result[0]

    if current_quantity < quantity:
        await ctx.send("<a:no:1330115448766988288> У вас недостаточно предметов для использования.")
        conn.close()
        return

    # Используем предмет (уменьшаем количество)
    new_quantity = current_quantity - quantity
    if new_quantity > 0:
        cursor.execute("""
        UPDATE inv SET quantity = ? WHERE user_id = ? AND item_name = ?
        """, (new_quantity, user_id, item_name))
    else:
        # Если количество предмета стало 0, удаляем его из инвентаря
        cursor.execute("""
        DELETE FROM inv WHERE user_id = ? AND item_name = ?
        """, (user_id, item_name))

    conn.commit()
    conn.close()

    await ctx.send(f"<a:yes:1330115480069083208> Вы использовали {quantity} {item_name}.")



@bot.command()
@has_role_for_command()
async def take_item(ctx, member: discord.Member):
    """Забрать технику у игрока и полностью удалить запись о предмете из инвентаря."""
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    # Берем инвентарь указанного игрока
    cursor.execute("""
    SELECT item_name, quantity FROM inv WHERE user_id = ?
    """, (str(member.id),))
    inventory = cursor.fetchall()

    if not inventory:
        embed = discord.Embed(
            description=f"<a:no:1330115448766988288> У игрока {member.display_name} нет техники в инвентаре.",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        await ctx.send(embed=embed)  
        conn.close()
        return  # Завершаем выполнение команды, если инвентарь пуст

    # Формируем эмбэд с инвентарём
    inventory_list = "\n".join([f"{i+1}. {item[0]} - {item[1]} шт." for i, item in enumerate(inventory)])
    embed = discord.Embed(
        title=f"Инвентарь игрока {member.display_name}",
        description=f"Выберите технику, которую хотите забрать:\n{inventory_list}",
        color=discord.Color.from_rgb(47, 49, 54)
    )


    message = await ctx.send(embed=embed)

    # Ожидаем ответа игрока с выбором техники
    def check(msg):
        return msg.author == ctx.author and msg.content.isdigit() and 1 <= int(msg.content) <= len(inventory)

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        selected_item_index = int(msg.content) - 1
        selected_item_name = inventory[selected_item_index][0]


        cursor.execute("""
        DELETE FROM inv WHERE user_id = ? AND item_name = ?
        """, (str(member.id), selected_item_name))
        conn.commit()


        embed = discord.Embed(
            description=f"<:emoji_77:1330875368575602740> Вы забрали предмет **{selected_item_name}** у {member.display_name}.",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        await ctx.send(embed=embed)

    except asyncio.TimeoutError:

        embed = discord.Embed(
            description="<a:no:1330115448766988288> Время для выбора истекло.",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        await ctx.send(embed=embed)

    finally:
        conn.close()


class InfoView(discord.ui.View):
    """Класс, объединяющий кнопки 'Параметры' и 'Экономика'"""
    def __init__(self, author, is_owner):
        super().__init__()
        self.author = author
        self.is_owner = is_owner


        for item in self.children:
            item.disabled = not is_owner

    @discord.ui.button(label="Параметры", style=discord.ButtonStyle.secondary)
    async def parameters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.defer()
            await interaction.followup.send("Вы не можете изменить параметры другого игрока!", ephemeral=True)
            return
        
        view = ChoiceView(self.author)
        embed = discord.Embed(title="Что вы хотите изменить?", color=discord.Color.dark_gray())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Экономика", style=discord.ButtonStyle.secondary)
    async def eco_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.defer()
            await interaction.followup.send("Вы не можете изменять экономику другого игрока!", ephemeral=True)
            return
        
        embed = discord.Embed(title="Экономическая информация", color=discord.Color.from_rgb(47, 49, 54))
        view = EconomyView(self.author)  
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ChoiceView(discord.ui.View):
    """Выбор параметра (Религия, Идеология, Форма правления)"""
    def __init__(self, author):
        super().__init__()
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.author

    @discord.ui.button(label="Религия", style=discord.ButtonStyle.primary)
    async def religion_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_options(interaction, "Религия", [""])

    @discord.ui.button(label="Идеология", style=discord.ButtonStyle.primary)
    async def ideology_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_options(interaction, "Идеология", [""])

    @discord.ui.button(label="Форма правления", style=discord.ButtonStyle.primary)
    async def government_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_options(interaction, "Форма правления", [""])

    async def show_options(self, interaction: discord.Interaction, title, options):
        embed = discord.Embed(title=f"Выберите {title}", color=discord.Color.from_rgb(47, 49, 54))
        for idx, option in enumerate(options):
            embed.add_field(name=str(idx + 1), value=option, inline=False)
        view = NumberedButtonsView(self.author, options)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class NumberedButtonsView(discord.ui.View):
    """Кнопки с номерами для выбора"""
    def __init__(self, author, options):
        super().__init__()
        self.author = author
        self.options = options
        for i in range(len(options)):
            self.add_item(NumberButton(i + 1, options[i]))

class NumberButton(discord.ui.Button):
    """Одна кнопка с номером"""
    def __init__(self, number, value):
        super().__init__(label=str(number), style=discord.ButtonStyle.primary)
        self.number = number
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Вы выбрали: {self.value}", ephemeral=True)


class EconomyView(discord.ui.View):
    """Кнопки для экономических параметров"""
    def __init__(self, author):
        super().__init__()
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.author

    @discord.ui.button(label="Промышленность", style=discord.ButtonStyle.primary)
    async def industry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_economy_info(interaction, "Промышленность")

    @discord.ui.button(label="Торговля", style=discord.ButtonStyle.primary)
    async def trade_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_economy_info(interaction, "Торговля")

    @discord.ui.button(label="Инфраструктура", style=discord.ButtonStyle.primary)
    async def infrastructure_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_economy_info(interaction, "Инфраструктура")

    async def send_economy_info(self, interaction: discord.Interaction, category):
        embed = discord.Embed(title=f"{category}", description="test", color=discord.Color.from_rgb(47, 49, 54))
        await interaction.response.send_message(embed=embed, ephemeral=True)



@bot.command()
async def info(ctx, member: discord.Member = None):
    """Вывод информации с кнопками 'Параметры' и 'Экономика'"""
    if member is None:
        member = ctx.author  

    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, ideology, religion, government, balance FROM players WHERE id = ?", (member.id,))
    data = cursor.fetchone()
    conn.close()

    if data is None:
        await ctx.send(f"{member.mention}, у тебя нет данных в базе!")
        return

    nickname, ideology, religion, government, balance = data

    embed = discord.Embed(color=discord.Color.from_rgb(47, 49, 54))
    embed.add_field(name="Nickname", value=nickname, inline=False)
    embed.add_field(name="Идеология", value=ideology, inline=False)
    embed.add_field(name="Религия", value=religion, inline=False)
    embed.add_field(name="Форма правления", value=government, inline=False)
    embed.add_field(name="Баланс", value=f'{balance} 💰', inline=False)
    embed.set_author(name=f"Информация об игроке {nickname}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)


    is_owner = ctx.author == member

    view = InfoView(ctx.author, is_owner)

    await ctx.send(embed=embed, view=view)









def fetch_data(guild_id):
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, season, end_season, last_update FROM guild_data WHERE guild_id = ?", (guild_id,))
    data = cursor.fetchone()
    conn.close()

    if not data:
        insert_default_data(guild_id)
        return fetch_data(guild_id)
    return data


def update_or_insert_data(guild_id, **kwargs):
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()

    for key, value in kwargs.items():
        cursor.execute(f"UPDATE guild_data SET {key} = ? WHERE guild_id = ?", (value, guild_id))

    conn.commit()
    conn.close()


def insert_default_data(guild_id):
    conn = sqlite3.connect("central.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO guild_data (guild_id) VALUES (?)", (guild_id,))
    conn.commit()
    conn.close()


@bot.command()
@has_role_for_command()
async def date(ctx, new_date: int):
    update_or_insert_data(ctx.guild.id, date=new_date)
    date_channel = discord.utils.get(ctx.guild.voice_channels, id=ALLOWED_CHANNELS["date"])
    if date_channel:
        await date_channel.edit(name=f"║🗓Year: {new_date}")
        await ctx.send(f"Дата обновлена: {new_date}")
    else:
        await ctx.send("Канал 'Дата' не найден!")


@bot.command()
@has_role_for_command()
async def end_se(ctx, days: int):
    update_or_insert_data(ctx.guild.id, end_season=days)
    end_season_channel = discord.utils.get(ctx.guild.voice_channels, id=ALLOWED_CHANNELS["end_season"])
    if end_season_channel:
        await end_season_channel.edit(name=f"║⌚The end Wipe: {days} d")
        await ctx.send(f"Конец сезона установлен: {days} дней")
    else:
        await ctx.send("Канал 'Конец Сезона' не найден!")


@bot.command()
@has_role_for_command()
async def season(ctx, new_season: int):
    update_or_insert_data(ctx.guild.id, season=new_season)
    season_channel = discord.utils.get(ctx.guild.voice_channels, id=ALLOWED_CHANNELS["season"])
    if season_channel:
        await season_channel.edit(name=f"╔💾Wipe: {new_season}")
        await ctx.send(f"Сезон обновлён: {new_season}")
    else:
        await ctx.send("Канал 'Сезон' не найден!")

@tasks.loop(hours=24)
async def daily_update():
    for guild in bot.guilds:
        data = fetch_data(guild.id)
        if not data:
            continue

        
        try:
            last_update = int(time.mktime(datetime.strptime(data[3], "%Y-%m-%d %H:%M:%S").timetuple())) if data[3] else 0
        except ValueError:
            last_update = 0  

        current_time = int(time.time())

        if last_update and (current_time - last_update) < 86400:  
            continue

        new_date = data[0] + 1
        new_end_season = max(0, data[2] - 1)

        update_or_insert_data(guild.id, date=new_date, end_season=new_end_season, last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        date_channel = discord.utils.get(guild.voice_channels, id=ALLOWED_CHANNELS["date"])
        if date_channel:
            await date_channel.edit(name=f"║🗓Year: {new_date}")

        end_season_channel = discord.utils.get(guild.voice_channels, id=ALLOWED_CHANNELS["end_season"])
        if end_season_channel:
            await end_season_channel.edit(name=f"║⌚The end Wipe: {new_end_season} d")

        print(f"✅ Обновлено для сервера {guild.id}: Дата -> {new_date}, Конец сезона -> {new_end_season}")

@daily_update.before_loop
async def before_daily_update():
    await bot.wait_until_ready()
    print("✅ Задача daily_update запущена!")




@tasks.loop(minutes=5)
async def update_community_channel():
    for guild in bot.guilds:
        community_channel = discord.utils.get(guild.voice_channels, id=ALLOWED_CHANNELS["community"])
        if community_channel:
            await community_channel.edit(name=f"╚🌍Members: {guild.member_count}")

@update_community_channel.before_loop
async def before_update_community():
    await bot.wait_until_ready()
    print("✅ Обновление Community запущено!")



class EconomyView(discord.ui.View):
    """Меню с выбором категории экономики"""
    def __init__(self):
        super().__init__()
        self.add_item(EconomySelect())

class EconomySelect(discord.ui.Select):
    """Выпадающее меню для выбора категории экономики"""
    def __init__(self):
        options = [
            discord.SelectOption(label="Где я?", description="Информация о проекте", emoji="🏭"),
            discord.SelectOption(label="Команды", description="Информация о командах", emoji="📦"),
            discord.SelectOption(label="Экономика", description="Информация об экономике", emoji="🛤"),
        ]
        super().__init__(placeholder="Выберите категорию экономики", options=options)

    async def callback(self, interaction: discord.Interaction):
        """Отправляет эмбед в зависимости от выбранной категории"""
        category = self.values[0]

        if category == "Где я?":
            embed = discord.Embed(title="Где я?", description="Country Politican RP - Это сервер в жанре ВПИ-Военно Политические Игры,розвивайте страну,обьеденяйтесь с другими игроками против общего врага.И захватите мир:)", color=discord.Color.blue())
            embed.add_field(name="None", value="none")
            embed.add_field(name="None", value="none")

        elif category == "Команды":
            embed = discord.Embed(title="📦 Команды", description="Информация о командах", color=discord.Color.green())


        elif category == "Экономика":
            embed = discord.Embed(title="🛤 Экономика", description="Информация об экономике", color=discord.Color.orange())
            embed.add_field(name="Дороги", value="Состояние дорог и железнодорожных путей.")
            embed.add_field(name="Энергетика", value="Уровень развития энергетической сети.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def send_faq(ctx, channel: discord.TextChannel):
    """Отправляет сообщение с меню выбора категории экономики в указанный канал"""
    embed = discord.Embed(
        title="FAQ", 
        description="Данный канал предназначаеться для новичков который впервые на сервере. Здесь вы можете ознакомиться со всей информацией для игры на сервере.", 
        color=discord.Color.from_rgb(47, 49, 54)
        )
    embed.add_field(name="Часто задаваемые вопросы:", value="Что такое ВПИ? Ответ: Военно Политические Игры,ознакомиться подробнее можете в разделе 'Где я'", inline=False)
        
    view = EconomyView()
    await channel.send(embed=embed, view=view)
    await ctx.send(f"Сообщение отправлено в {channel.mention}", ephemeral=True)



























bot.run (BOT_TOKEN)
