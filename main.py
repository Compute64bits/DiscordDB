from discord.ext import commands
from os import path
import sqlite3
import asyncio

bot = commands.Bot(command_prefix='!!', self_bot=True)

with open('token.txt', 'r') as f:
    token = f.read()

@bot.event
async def on_ready():
    print('------')
    print('Logged in as ' + str(bot.user.name) + " (" + str(bot.user.id) + ")")
    print('------')

    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()

    if not path.exists('db.sqlite'):
        c.execute('''CREATE TABLE members (id text, display_name text, username text, badges text, created_at text, source text)''')
        conn.commit()
        print("[+] Database created successfully!")

    print("[+] Cleaning database...")
    c.execute(f"DELETE FROM members WHERE id = ?", (str(bot.user.id),))
    conn.commit()
    conn.close()

    print("[+] Scanning messages...")

async def writter(member, server: str):
    member_id = f"{member.id}"

    if member_id == str(bot.user.id):
        return False

    username_bytes = member.name + "#" + member.discriminator

    badges = []
    if member.bot:
        badges.append("Bot")
    elif member.premium_since is not None:
        badges.append("Nitro")
    badges += member.public_flags.all()
    badges = str(badges)

    created_at = f"{member.created_at.strftime('%d/%m/%Y %H:%M:%S')}"

    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()

    c.execute(f"SELECT * FROM members WHERE id = '{member_id}'")
    member_info = c.fetchone()

    good = False

    if member_info is None:
        c.execute(f"INSERT INTO members VALUES (?, ?, ?, ?, ?, ?)", (member_id, member.display_name, username_bytes, badges, created_at, str(server)))
        good = True
    else:
        if  member.display_name not in str(member_info[1]):
            c.execute(f"UPDATE members SET display_name = ? WHERE id = ?", (f'{str(member_info[1])} ;;; {str(member.display_name)}', member_id))
            good = True
        if  username_bytes not in str(member_info[2]):
            c.execute(f"UPDATE members SET username = ? WHERE id = ?", (f'{str(member_info[2])} ;;; {str(username_bytes)}', member_id))
            good = True
        if  badges not in str(member_info[3]):
            c.execute(f"UPDATE members SET badges = ? WHERE id = ?", (f'{str(member_info[3])} ;;; {badges}', member_id))
            good = True
        if  created_at not in str(member_info[4]):
            c.execute(f"UPDATE members SET created_at = ? WHERE id = ?", (f'{str(member_info[4])} ;;; {str(created_at)}', member_id))
            good = True
        if server not in str(member_info[5]):
            c.execute(f"UPDATE members SET source = ? WHERE id = ?", (f'{str(member_info[5])} ;;; {str(server)}', member_id))
            good = True

    conn.commit()
    conn.close()

    return good

threads = []

@bot.command(pass_context=True)
async def ga(ctx, time_min, first=True):
    global threads

    if(first):
        await ctx.message.delete()
        threads += [f"{ctx.guild.id}{ctx.channel.id}"]

    if f"{ctx.guild.id}{ctx.channel.id}" not in threads:
        return

    if(time_min is None):
        print("[-] !!ga <time>   - Please specify a time in minutes!")
        print("    example: !!ga 2")

    time_min = int(time_min)
    server = str(ctx.guild)

    total = 0
    for member in ctx.guild.members:
        if(await writter(member, server)):
            total += 1
    
    print(f"+ {total} from {server.encode('utf-8')}")

    await asyncio.sleep(time_min*60)
    await ga(ctx, time_min, False)

@bot.command(pass_context=True)
async def kill(ctx):
    global threads

    await ctx.message.delete()

    if f"{ctx.guild.id}{ctx.channel.id}" in threads:
        threads.remove(f"{ctx.guild.id}{ctx.channel.id}")
        print(f"[-] Stopped scanning {ctx.guild.name.encode('utf-8')}")

@bot.command(pass_context=True)
async def uga(ctx):

    await ctx.message.delete()

    server = str(ctx.guild)

    total = 0
    for member in ctx.guild.members:
        if(await writter(member, server)):
            total += 1

    print(f"+ {total} from {server.encode('utf-8')}")


@bot.event
async def on_message(message):

    if message.author.id == bot.user.id:
        await bot.process_commands(message)
        return
    
    server = str(message.guild)
    if message.guild is None:
        return
        
    member = message.guild.get_member(message.author.id)
        
    if member is None:
        return

    await writter(member, server)

bot.run(token)
